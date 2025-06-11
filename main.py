from flask import Flask, request, jsonify, render_template_string
import requests
import base64

app = Flask(__name__)
API_TOKEN = "LKST9CV9IGMWHW2J7SFI"

HTML_PAGE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Image Geolocator</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="https://unpkg.com/leaflet/dist/leaflet.css" />
    <style>
        body {
            margin: 0;
            font-family: 'Inter', sans-serif;
            background: #f1f3f5;
        }
        .container {
            display: flex;
            height: 100vh;
        }
        .left {
            width: 40%;
            padding: 30px;
            background: white;
            box-shadow: 2px 0 8px rgba(0,0,0,0.1);
            overflow-y: auto;
        }
        .right {
            flex: 1;
        }
        h2 {
            font-weight: 600;
        }
        button {
            background-color: #007bff;
            color: white;
            border: none;
            padding: 12px 20px;
            border-radius: 8px;
            font-size: 16px;
            cursor: pointer;
            transition: background 0.2s;
            margin-top: 10px;
        }
        button:hover {
            background-color: #0056b3;
        }
        #map {
            width: 100%;
            height: 100%;
        }
        #result p {
            margin-bottom: 10px;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="left">
            <center><h2>Located</h2>
            <input type="file" id="imageInput"><br>
            <button onclick="sendImage()">Locate Image</button>
            <div id="result"></div>
        </div>
        <div class="right">
            <div id="map"></div>
        </div>
    </div>

    <script src="https://unpkg.com/leaflet/dist/leaflet.js"></script>
    <script src="https://unpkg.com/leaflet.heat/dist/leaflet-heat.js"></script>
    <script>
        let map = L.map('map').setView([20, 0], 2);
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            maxZoom: 18
        }).addTo(map);
        let heatLayer;

        async function sendImage() {
            const fileInput = document.getElementById("imageInput");
            const resultDiv = document.getElementById("result");

            resultDiv.innerHTML = "Locating...";

            if (!fileInput.files.length) {
                alert("Please upload an image.");
                return;
            }

            const formData = new FormData();
            formData.append("image", fileInput.files[0]);

            const response = await fetch("/api/geolocate", {
                method: "POST",
                body: formData
            });

            const data = await response.json();
            resultDiv.innerHTML = "";

            if (data.topk_predictions_dict) {
                resultDiv.innerHTML = "<h3>Top Predictions:</h3>";
                const heatPoints = [];

                for (const [rank, pred] of Object.entries(data.topk_predictions_dict)) {
                    const addr = pred.address;
                    const gps = pred.gps;
                    const conf = pred.confidence;
                    resultDiv.innerHTML += `<p><strong>${rank}.</strong> ${addr.city}, ${addr.country}<br>Lat: ${gps[0]}, Lon: ${gps[1]}<br>Confidence: ${(conf * 100).toFixed(2)}%</p>`;
                    heatPoints.push([gps[0], gps[1], conf]);
                }

                if (heatLayer) map.removeLayer(heatLayer);
                heatLayer = L.heatLayer(heatPoints, {radius: 25, blur: 20, maxZoom: 10});
                heatLayer.addTo(map);
                map.setView(heatPoints[0].slice(0, 2), 7);
            } else {
                resultDiv.innerHTML = `<p>Error: ${data.error || "No predictions found."}</p>`;
            }
        }
    </script>
</body>
</html>
"""

@app.route("/")
def index():
    return render_template_string(HTML_PAGE)

@app.route("/api/geolocate", methods=["POST"])
def geolocate_image():
    if 'image' not in request.files:
        return jsonify({"error": "No image uploaded"}), 400

    image = request.files['image']
    encoded_image = base64.b64encode(image.read()).decode('utf-8')

    payload = {
        "TOKEN": API_TOKEN,
        "IMAGE": encoded_image,
        "TOP_K": 10,
        "Center_LATITUDE": None,
        "Center_LONGITUDE": None,
        "RADIUS": None
    }

    headers = {"Content-Type": "application/json"}
    response = requests.post("https://picarta.ai/classify", json=payload, headers=headers)

    if response.status_code == 200:
        return jsonify(response.json())
    else:
        return jsonify({"error": "Picarta API failed", "status": response.status_code}), 500

if __name__ == "__main__":
    app.run(debug=True)
