import sys
import asyncio
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel, QTextEdit, QPushButton, QComboBox, QSlider, QFileDialog
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5 import QtGui
import edge_tts


class TTSWorker(QThread):
    finished = pyqtSignal(str)

    def __init__(self, text_list, output_list, selected_voice, pitch, rate):
        super().__init__()
        self.text_list = text_list
        self.output_list = output_list
        self.selected_voice = selected_voice
        self.pitch = pitch
        self.rate = rate

    async def text_to_speech(self, text, output_file):
        communicate = edge_tts.Communicate(text, voice=self.selected_voice, rate=self.rate, pitch=self.pitch)
        await communicate.save(output_file)
        return output_file

    async def process_texts(self):
        tasks = []
        for text, output_file in zip(self.text_list, self.output_list):
            tasks.append(self.text_to_speech(text, output_file))
        results = await asyncio.gather(*tasks)
        return results

    def run(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        results = loop.run_until_complete(self.process_texts())
        for result in results:
            self.finished.emit(result)


class TTSApp(QWidget):
    def __init__(self):
        super().__init__()
        self.output_directory = ""
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        # Label dan input teks
        self.text_input_label = QLabel('Masukkan Teks (Pisahkan dengan baris baru untuk teks yang berbeda):')
        self.text_input = QTextEdit()

        # Label dan input nama file output
        self.file_name_label = QLabel('Nama File Output (Pisahkan dengan baris baru untuk setiap teks):')
        self.file_name_input = QTextEdit()

        # Tombol untuk memilih direktori penyimpanan
        self.select_directory_button = QPushButton('Pilih Lokasi Penyimpanan')
        self.select_directory_button.clicked.connect(self.select_output_directory)

        self.selected_directory_label = QLabel('Lokasi penyimpanan: Belum dipilih')

        # Dropdown untuk memilih voice
        self.voice_label = QLabel('Pilih Voice:')
        self.voice_dropdown = QComboBox()

        #List Suara From : https://gist.github.com/BettyJJ/17cbaa1de96235a7f5773b8690a20462
        self.voices = {
            "id-ID-GadisNeural": "Gadis (Indonesia)""(Friendly, Positive)",
            "id-ID-ArdiNeural": "Ardi (Indonesia)""(Friendly, Positive)",
            "en-US-AriaNeural": "Aria (English US)""(Friendly, Positive)",
            "en-AU-NatashaNeural": "Natasha (English AU)""(Friendly, Positive)",
            "en-AU-WilliamNeural": "William (English AU)""(Friendly, Positive)",
            "en-CA-ClaraNeural": "Clara (English CA)""(Friendly, Positive)",
            "en-CA-LiamNeural": "Liam (English CA)""(Friendly, Positive)",
            "en-HK-SamNeural": "Sam (English HK)""(Friendly, Positive)",
            "en-HK-YanNeural": "Yan (English HK)""(Friendly, Positive)",
            "en-IN-NeerjaNeural": "Neerja (English IN)""(Friendly, Positive)",
            "en-IN-PrabhatNeural": "Prabhat (English IN)""(Rational)",
            "en-US-GuyNeural": "Guy (English IN)""(Passion)",
            "en-US-JennyNeural": "Jenny (English US)""(Friendly, Considerate, Comfort)",
            "en-US-EricNeural": "Eric (English US)""(Rational)",
            "en-GB-RyanNeural": "Ryan (English UK)""(Friendly, Positive)",
            "en-US-MichelleNeural": "Michelle (English US)""(Friendly, Pleasant)",
            "en-US-RogerNeural": "Roger (English US)""(Lively)",
            "en-IN-NeerjaNeural": "Neerja (English India)""(Friendly, Positive)"
        }

        # Tambahkan suara ke pilihan dropdown
        for voice, label in self.voices.items():
            self.voice_dropdown.addItem(label, voice)

        # Slider untuk pitch
        self.pitch_label = QLabel('Pitch (Range: -50Hz to +50Hz):')
        self.pitch_slider = QSlider(Qt.Horizontal)
        self.pitch_slider.setMinimum(-50)
        self.pitch_slider.setMaximum(50)
        self.pitch_slider.setValue(0)
        self.pitch_slider.setTickPosition(QSlider.TicksBelow)
        self.pitch_slider.setTickInterval(10)
        self.pitch_value_label = QLabel('Current Pitch: 0Hz')
        self.pitch_slider.valueChanged.connect(self.update_pitch_value)

        # Slider untuk kecepatan
        self.rate_label = QLabel('Kecepatan (Range: -50% to +50%):')
        self.rate_slider = QSlider(Qt.Horizontal)
        self.rate_slider.setMinimum(-50)
        self.rate_slider.setMaximum(50)
        self.rate_slider.setValue(0)
        self.rate_slider.setTickPosition(QSlider.TicksBelow)
        self.rate_slider.setTickInterval(10)
        self.rate_value_label = QLabel('Current Rate: 0%')
        self.rate_slider.valueChanged.connect(self.update_rate_value)

        # Tombol untuk memulai proses TTS
        self.process_button = QPushButton('Proses Teks Menjadi Suara')
        self.process_button.clicked.connect(self.start_tts_processing)
        self.result_label = QLabel('Status: Menunggu proses...')

        # Susunan Widget
        layout.addWidget(self.text_input_label)
        layout.addWidget(self.text_input)
        layout.addWidget(self.file_name_label)
        layout.addWidget(self.file_name_input)
        layout.addWidget(self.select_directory_button)
        layout.addWidget(self.selected_directory_label)
        layout.addWidget(self.voice_label)
        layout.addWidget(self.voice_dropdown)
        layout.addWidget(self.pitch_label)
        layout.addWidget(self.pitch_slider)
        layout.addWidget(self.pitch_value_label)
        layout.addWidget(self.rate_label)
        layout.addWidget(self.rate_slider)
        layout.addWidget(self.rate_value_label)
        layout.addWidget(self.process_button)
        layout.addWidget(self.result_label)

        # Pengaturan Utama Main Window
        self.setLayout(layout)
        self.setWindowTitle('MY-Teks-to-Speech-App')
        self.setWindowIcon(QtGui.QIcon('logo.png'))
        self.setGeometry(300, 300, 400, 600)

    def update_pitch_value(self, value):
        """Update the pitch value label with the current slider value."""
        self.pitch_value_label.setText(f'Current Pitch: {value}Hz')

    def update_rate_value(self, value):
        """Update the rate value label with the current slider value."""
        self.rate_value_label.setText(f'Current Rate: {value}%')

    def select_output_directory(self):
        """Open a dialog to select the output directory."""
        directory = QFileDialog.getExistingDirectory(self, 'Pilih Lokasi Penyimpanan')
        if directory:
            self.output_directory = directory
            self.selected_directory_label.setText(f'Lokasi penyimpanan: {directory}')

    def start_tts_processing(self):
        # Ambil teks dan nama file dari input user
        texts = self.text_input.toPlainText().strip().split('\n')
        output_files = self.file_name_input.toPlainText().strip().split('\n')

        # Ambil voice yang dipilih dari dropdown
        selected_voice = self.voice_dropdown.currentData()

        # Ambil pitch dan rate dari slider
        pitch_value = int(self.pitch_slider.value())  # Konversi ke integer
        rate_value = int(self.rate_slider.value())  

        pitch = f"{pitch_value:+d}Hz"  # Pitch Wajib dari Library 'Hz'
        rate = f"{rate_value:+d}%" 

        # Validasi input
        if len(texts) != len(output_files):
            self.result_label.setText('Error: Jumlah teks dan nama file tidak sama!')
            return

        # Pastikan direktori penyimpanan telah dipilih
        if not self.output_directory:
            self.result_label.setText('Error: Lokasi penyimpanan belum dipilih!')
            return

        # Gabungkan nama file dengan direktori yang dipilih
        output_paths = [f"{self.output_directory}/{filename.strip()}" for filename in output_files]

        # Mulai proses
        self.result_label.setText('Proses sedang berjalan...')
        self.worker = TTSWorker(texts, output_paths, selected_voice, pitch, rate)
        self.worker.finished.connect(self.on_tts_finished)
        self.worker.start()

    def on_tts_finished(self, output_file):
        self.result_label.setText(f"Proses selesai! File disimpan: {output_file}")


# Eksekusi
if __name__ == '__main__':
    app = QApplication(sys.argv)
    tts_app = TTSApp()
    tts_app.show()
    sys.exit(app.exec_())
