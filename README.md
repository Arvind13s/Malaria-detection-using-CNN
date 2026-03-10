---
title: Malaria Detection
emoji: 🔬
colorFrom: green
colorTo: red
sdk: docker
pinned: false
---

# Malaria Detection Using CNN

This project is a web application that uses deep learning to detect malaria parasites from blood smear images. Users can upload microscopy images, and the system predicts whether the cell is **Parasitized** or **Uninfected** using a pre-trained Convolutional Neural Network.

## Features

* **Drag & Drop Upload:** Easily upload blood smear microscopy images for instant analysis.
* **AI-Powered Prediction:** Uses a CNN model trained on the NIH Malaria Cell Images dataset.
* **Confidence Scores:** Displays detailed probability breakdown with animated confidence bars.
* **Modern UI:** Dark-mode glassmorphism design with blood cell-themed background animations.
* **Responsive Design:** Optimized for both desktop and mobile viewing.
* **Informational Sections:** Includes How It Works and About sections for user guidance.

## Getting Started

### Prerequisites
* Python 3.9+
* pip

### Model File Note
The core model file (`my_model.keras`) is **not included** in this repository due to its large size. It will be **automatically downloaded from Google Drive** when you run the app for the first time.

### Local Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/Arvind13s/Malaria-detection-using-CNN.git
   cd Malaria-detection-using-CNN
   ```

2. **Install the required packages:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the Flask app:**
   ```bash
   python app.py
   ```

> **Note:** On the first run, the app will automatically download the model file from Google Drive. Locally, the app will be accessible at `http://127.0.0.1:5000/`.

## Usage

1. Navigate to the homepage of the web application.
2. Upload a blood smear microscopy image using drag & drop or click to browse.
3. Click the **"Analyze Image"** button to initiate the detection process.
4. View the AI's prediction results — **Parasitized** or **Uninfected** — with confidence scores.

## About the Model

The malaria detection model is a Convolutional Neural Network trained on the [NIH Malaria Cell Images](https://www.kaggle.com/datasets/iarunava/cell-images-for-detecting-malaria) dataset. It classifies individual cell images as either containing *Plasmodium* parasites (**Parasitized**) or being free of infection (**Uninfected**).

## Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create a new branch (`git checkout -b feature-branch`)
3. Make your changes
4. Commit your changes (`git commit -m 'Add new feature'`)
5. Push to the branch (`git push origin feature-branch`)
6. Create a pull request

## Project Structure

```
Malaria-detection-using-CNN/
├── frontend/
│   ├── index.html
│   ├── style.css
│   └── script.js
├── models/
│   └── my_model.keras (downloaded automatically)
├── app.py
├── Dockerfile
├── Malaria.ipynb
├── requirements.txt
├── .gitignore
├── LICENSE
└── README.md
```

## License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.

## Acknowledgments

* **[Flask](https://flask.palletsprojects.com/)** — The web framework used.
* **[TensorFlow / Keras](https://www.tensorflow.org/)** — For building and training the CNN model.
* **[NIH Malaria Dataset](https://www.kaggle.com/datasets/iarunava/cell-images-for-detecting-malaria)** — The dataset used for training.

## Disclaimer

⚠️ This tool is intended for **educational and research purposes only**. It is not a certified medical device and should not be used for clinical diagnosis.
