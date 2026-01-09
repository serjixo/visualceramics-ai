import gc
import io
import os
import time
import uuid
import cv2
import numpy as np
import torch
from PIL import Image
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from transformers import Sam3Processor, Sam3Model

app = FastAPI(title="VisualCeramics AI Engine")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuración de rutas
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(BASE_DIR, "static", "masks")
os.makedirs(OUTPUT_DIR, exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")

# --- CARGA DEL MODELO ---
# Forzamos MPS (GPU Apple) si está disponible
device = torch.device("mps" if torch.backends.mps.is_available() else "cpu")
print(f"🚀 Iniciando servidor. Dispositivo: {device}")

start_load = time.time()
# Cargamos el modelo en float16 para que ocupe la mitad de memoria y sea más rápido en Mac
model = Sam3Model.from_pretrained("facebook/sam3", torch_dtype=torch.float16).to(device)
processor = Sam3Processor.from_pretrained("facebook/sam3")
print(f"✅ Modelo cargado en {time.time() - start_load:.2f} segundos.")

def clean_memory():
    if device.type == "mps":
        torch.mps.empty_cache()
    gc.collect()

@app.post("/api/v1/analyze")
async def analyze_scene(file: UploadFile = File(...)):
    start_total = time.time()
    try:
        # 1. Leer imagen
        image_bytes = await file.read()
        raw_image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        original_size = raw_image.size
        job_id = str(uuid.uuid4())

        # 2. Redimensionar para la IA (Crucial para velocidad)
        MAX_SIZE = 1024
        ratio = MAX_SIZE / max(original_size)
        new_size = (int(original_size[0] * ratio), int(original_size[1] * ratio))
        input_image = raw_image.resize(new_size, Image.LANCZOS)

        print(f"\n📸 [{job_id}] IA trabajando a {new_size[0]}x{new_size[1]} (Original: {original_size[0]}x{original_size[1]})")

        results_map = {}
        labels = ["floor", "wall"]

        for label in labels:
            start_ai = time.time()
            print(f"🔍 [{job_id}] Buscando: {label}...")

            # Procesar inputs
            inputs = processor(images=input_image, text=label, return_tensors="pt").to(device)
            # Pasamos los inputs a float16 para coincidir con el modelo
            inputs = {k: v.to(torch.float16) if v.dtype == torch.float32 else v for k, v in inputs.items()}

            with torch.no_grad():
                outputs = model(**inputs)

            # Post-proceso a tamaño PEQUEÑO (new_size) para que sea instantáneo
            results = processor.post_process_instance_segmentation(
                outputs,
                threshold=0.4,
                target_sizes=[new_size[::-1]]
            )[0]

            # --- INDENTACIÓN CORREGIDA: ESTO DEBE ESTAR DENTRO DEL FOR ---
            if len(results['masks']) > 0:
                mask = torch.sum(results['masks'], dim=0).clamp(0, 1).cpu().numpy()
                filename = f"{job_id}_{label}.png"
                full_path = os.path.join(OUTPUT_DIR, filename)

                # Guardar máscara
                cv2.imwrite(full_path, (mask * 255).astype(np.uint8))
                results_map[label] = f"/static/masks/{filename}"
                print(f"   ✅ {label.capitalize()} encontrado en {time.time() - start_ai:.2f}s")
            else:
                print(f"   ⚠️ {label.capitalize()} no detectado.")

            # Limpiar memoria de la iteración actual
            del outputs
            clean_memory()
            # --- FIN DEL BLOQUE DENTRO DEL FOR ---

        # 3. Shadow Map (usamos la imagen original pero la guardamos rápido con OpenCV)
        start_shadow = time.time()
        shadow_file = f"{job_id}_shadows.png"
        shadow_path = os.path.join(OUTPUT_DIR, shadow_file)

        # Opcional: redimensionar el shadow map para no saturar el ancho de banda del cliente
        gray = cv2.cvtColor(np.array(raw_image), cv2.COLOR_RGB2GRAY)
        cv2.imwrite(shadow_path, gray)
        print(f"🌑 [{job_id}] Shadow Map generado en {time.time() - start_shadow:.2f}s")

        total_time = time.time() - start_total
        print(f"✨ [{job_id}] COMPLETADA EN: {total_time:.2f}s")
        print("-" * 50)

        return {
            "jobId": job_id,
            "processing_time": f"{total_time:.2f}s",
            "masks": results_map,
            "shadows": f"/static/masks/{shadow_file}"
        }

    except Exception as e:
        clean_memory()
        print(f"❌ Error en petición {job_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)