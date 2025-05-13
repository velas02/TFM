// MainWindow.xaml.cs
using System;
using System.IO;
using System.Net.Http;
using System.Threading.Tasks;
using System.Windows;
using Microsoft.Win32;

namespace TFMUI
{
    public partial class MainWindow : Window
    {
        private string _csvFilePath = string.Empty;

        public MainWindow()
        {
            InitializeComponent();
        }

        // arrastre sobre la zona
        private void CsvDropZone_DragOver(object sender, DragEventArgs e)
        {
            e.Handled = true;
            e.Effects = e.Data.GetDataPresent(DataFormats.FileDrop)
                        ? DragDropEffects.Copy
                        : DragDropEffects.None;
        }

        // al soltar archivo
        private void CsvDropZone_Drop(object sender, DragEventArgs e)
        {
            if (e.Data.GetDataPresent(DataFormats.FileDrop))
            {
                var files = (string[])e.Data.GetData(DataFormats.FileDrop);
                if (files.Length > 0 &&
                    Path.GetExtension(files[0])
                        .Equals(".csv", StringComparison.OrdinalIgnoreCase))
                {
                    SetCsvFile(files[0]);
                }
            }
        }

        // al hacer clic, abrir diálogo
        private void CsvDropZone_Click(object sender, System.Windows.Input.MouseButtonEventArgs e)
        {
            var dlg = new OpenFileDialog
            {
                Filter = "Archivos CSV (*.csv)|*.csv",
                Title = "seleccionar archivo csv"
            };
            if (dlg.ShowDialog() == true)
            {
                SetCsvFile(dlg.FileName);
            }
        }

        // almacena la ruta y actualiza el texto
        private void SetCsvFile(string path)
        {
            _csvFilePath = path;
            txtDropZone.Text = $"archivo: {Path.GetFileName(path)}";
        }

        // al pulsar enviar
        private async void SendCsvButton_Click(object sender, RoutedEventArgs e)
        {
            if (string.IsNullOrEmpty(_csvFilePath))
            {
                MessageBox.Show("primero seleccione un archivo csv",
                                "advertencia",
                                MessageBoxButton.OK,
                                MessageBoxImage.Warning);
                return;
            }

            try
            {
                await UploadCsvAsync(_csvFilePath);
                MessageBox.Show("csv enviado correctamente",
                                "éxito",
                                MessageBoxButton.OK,
                                MessageBoxImage.Information);
            }
            catch (Exception ex)
            {
                MessageBox.Show($"error al enviar csv: {ex.Message}",
                                "error",
                                MessageBoxButton.OK,
                                MessageBoxImage.Error);
            }
        }

        // método de subida: multipart/form-data al endpoint predict_csv
        private async Task UploadCsvAsync(string filePath)
        {
            using var client = new HttpClient();
            using var content = new MultipartFormDataContent();
            var stream = File.OpenRead(filePath);
            content.Add(new StreamContent(stream), "file", Path.GetFileName(filePath));

            // ajusta la url al endpoint de tu API que procese csv
            var response = await client.PostAsync("http://localhost:5000/predict_svm", content);
            response.EnsureSuccessStatusCode();
        }
    }
}
