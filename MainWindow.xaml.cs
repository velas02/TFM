// MainWindow.xaml.cs
using System;
using System.Collections.ObjectModel;
using System.IO;
using System.Linq;
using System.Net.Http;
using System.Text;
using System.Threading.Tasks;
using System.Windows;
using System.Windows.Input;
using Microsoft.Win32;
using Newtonsoft.Json;

namespace TFMUI
{
    public partial class MainWindow : Window
    {
        private string _csvFilePath = string.Empty;
        private ObservableCollection<ColumnDescription> _sampleData = new ObservableCollection<ColumnDescription>();

        public MainWindow()
        {
            InitializeComponent();
            cargarDatosDeEjemplo();
        }

        private void cargarDatosDeEjemplo()
        {
            _sampleData = new ObservableCollection<ColumnDescription>
            {
                new ColumnDescription { Column = "Unnamed: 0", Description = "Índice original del csv" },
                new ColumnDescription { Column = "state_code", Description = "Código del estado" },
                new ColumnDescription { Column = "latitude", Description = "Latitud" },
                new ColumnDescription { Column = "longitude", Description = "Longitud" },
                new ColumnDescription { Column = "zip_code", Description = "Código postal" },
                new ColumnDescription { Column = "id", Description = "Identificador de la empresa" },
                new ColumnDescription { Column = "city", Description = "Ciudad" },
                new ColumnDescription { Column = "Unnamed: 6", Description = "Columna vacía o sin nombre" },
                new ColumnDescription { Column = "name", Description = "Nombre de la empresa" },
                new ColumnDescription { Column = "labels", Description = "Etiquetas asociadas" },
                new ColumnDescription { Column = "founded_at", Description = "Fecha de fundación" },
                new ColumnDescription { Column = "closed_at", Description = "Fecha de cierre" },
                new ColumnDescription { Column = "first_funding_at", Description = "Fecha de primera financiación" },
                new ColumnDescription { Column = "last_funding_at", Description = "Fecha de última financiación" },
                new ColumnDescription { Column = "age_first_funding_year", Description = "Años hasta la primera financiación" },
                new ColumnDescription { Column = "age_last_funding_year", Description = "Años hasta la última financiación" },
                new ColumnDescription { Column = "age_first_milestone_year", Description = "Años hasta el primer hito" },
                new ColumnDescription { Column = "age_last_milestone_year", Description = "Años hasta el último hito" },
                new ColumnDescription { Column = "relationships", Description = "Número de relaciones clave" },
                new ColumnDescription { Column = "funding_rounds", Description = "Número de rondas de financiación" },
                new ColumnDescription { Column = "funding_total_usd", Description = "Financiación total en usd" },
                new ColumnDescription { Column = "milestones", Description = "Número de hitos" },
                new ColumnDescription { Column = "state_code.1", Description = "Código del estado (duplicado)" },
                new ColumnDescription { Column = "is_CA", Description = "Indica si está en california" },
                new ColumnDescription { Column = "is_NY", Description = "Indica si está en nueva york" },
                new ColumnDescription { Column = "is_MA", Description = "Indica si está en massachusetts" },
                new ColumnDescription { Column = "is_TX", Description = "Indica si está en texas" },
                new ColumnDescription { Column = "is_otherstate", Description = "Indica si está en otro estado" },
                new ColumnDescription { Column = "category_code", Description = "Categoría principal" },
                new ColumnDescription { Column = "is_software", Description = "Pertenece al sector software" },
                new ColumnDescription { Column = "is_web", Description = "Pertenece al sector web" },
                new ColumnDescription { Column = "is_mobile", Description = "Pertenece al sector móvil" },
                new ColumnDescription { Column = "is_enterprise", Description = "Pertenece al sector empresarial" },
                new ColumnDescription { Column = "is_advertising", Description = "Pertenece al sector publicidad" },
                new ColumnDescription { Column = "is_gamesvideo", Description = "Pertenece al sector videojuegos o medios" },
                new ColumnDescription { Column = "is_ecommerce", Description = "Pertenece al sector comercio electrónico" },
                new ColumnDescription { Column = "is_biotech", Description = "Pertenece al sector biotecnología" },
                new ColumnDescription { Column = "is_consulting", Description = "Pertenece al sector consultoría" },
                new ColumnDescription { Column = "is_othercategory", Description = "Pertenece a otra categoría" },
                new ColumnDescription { Column = "object_id", Description = "Identificador alternativo" },
                new ColumnDescription { Column = "has_VC", Description = "Ha recibido capital de riesgo" },
                new ColumnDescription { Column = "has_angel", Description = "Ha recibido inversión ángel" },
                new ColumnDescription { Column = "has_roundA", Description = "Ha recibido financiación en ronda a" },
                new ColumnDescription { Column = "has_roundB", Description = "Ha recibido financiación en ronda b" },
                new ColumnDescription { Column = "has_roundC", Description = "Ha recibido financiación en ronda c" },
                new ColumnDescription { Column = "has_roundD", Description = "Ha recibido financiación en ronda d" },
                new ColumnDescription { Column = "avg_participants", Description = "Promedio de participantes por ronda" },
                new ColumnDescription { Column = "is_top500", Description = "Indica si está en el top 500" },
                new ColumnDescription { Column = "status", Description = "Estado actual de la empresa" }
            };

            dataGrid.ItemsSource = _sampleData;

        }

        private void CsvDropZone_DragOver(object sender, DragEventArgs e)
        {
            e.Handled = true;
            e.Effects = e.Data.GetDataPresent(DataFormats.FileDrop)
                        ? DragDropEffects.Copy
                        : DragDropEffects.None;
        }

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

        private void CsvDropZone_Click(object sender, MouseButtonEventArgs e)
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

        private void SetCsvFile(string path)
        {
            _csvFilePath = path;
            txtDropZone.Text = $"archivo: {Path.GetFileName(path)}";
        }

        // botón predicción SVM
        private async void PredictSvm_Click(object sender, RoutedEventArgs e)
        {
            if (string.IsNullOrEmpty(_csvFilePath))
            {
                MessageBox.Show("primero seleccione un archivo csv",
                                "advertencia",
                                MessageBoxButton.OK,
                                MessageBoxImage.Warning);
                return;
            }

            var result = await EnviarCsvYObtenerPrediccionAsync(_csvFilePath, "http://localhost:5000/predict_svm");
            MessageBox.Show($"predicción: {result.prediction}\nprobabilidad: {result.probability:F2}",
                            "resultado SVM",
                            MessageBoxButton.OK,
                            MessageBoxImage.Information);
        }

        // botón explicación SHAP con SVM
        private async void ShapSvm_Click(object sender, RoutedEventArgs e)
        {
            if (string.IsNullOrEmpty(_csvFilePath))
            {
                MessageBox.Show("primero seleccione un archivo csv",
                                "advertencia",
                                MessageBoxButton.OK,
                                MessageBoxImage.Warning);
                return;
            }

            var shap = await EnviarCsvYObtenerShapAsync(_csvFilePath, "http://localhost:5000/explain_svm");
            // aquí podrías formatear el diccionario shap para mostrarlo mejor
            var detalles = string.Join("\n", shap.Select(kv => $"{kv.Key}: {kv.Value:F3}"));
            MessageBox.Show(detalles,
                            "valores SHAP SVM",
                            MessageBoxButton.OK,
                            MessageBoxImage.Information);
        }

        // botón predicción MLP
        private async void PredictMlp_Click(object sender, RoutedEventArgs e)
        {
            if (string.IsNullOrEmpty(_csvFilePath))
            {
                MessageBox.Show("primero seleccione un archivo csv",
                                "advertencia",
                                MessageBoxButton.OK,
                                MessageBoxImage.Warning);
                return;
            }

            var result = await EnviarCsvYObtenerPrediccionAsync(_csvFilePath, "http://localhost:5000/predict_mlp");
            MessageBox.Show($"predicción: {result.prediction}\nprobabilidad: {result.probability:F2}",
                            "resultado MLP",
                            MessageBoxButton.OK,
                            MessageBoxImage.Information);
        }

        // botón explicación SHAP con MLP
        private async void ShapMlp_Click(object sender, RoutedEventArgs e)
        {
            if (string.IsNullOrEmpty(_csvFilePath))
            {
                MessageBox.Show("primero seleccione un archivo csv",
                                "advertencia",
                                MessageBoxButton.OK,
                                MessageBoxImage.Warning);
                return;
            }

            var shap = await EnviarCsvYObtenerShapAsync(_csvFilePath, "http://localhost:5000/shap_mlp");
            var detalles = string.Join("\n", shap.Select(kv => $"{kv.Key}: {kv.Value:F3}"));
            MessageBox.Show(detalles,
                            "valores SHAP MLP",
                            MessageBoxButton.OK,
                            MessageBoxImage.Information);
        }

        // lee CSV de una sola fila y envía JSON al endpoint de predicción
        private async Task<PredictionResult> EnviarCsvYObtenerPrediccionAsync(string filePath, string url)
        {
            var (headers, values) = LeerCabeceraYValores(filePath);
            var payload = ConstruirPayload(headers, values);

            using var client = new HttpClient();
            var json = JsonConvert.SerializeObject(payload);
            var content = new StringContent(json, Encoding.UTF8, "application/json");
            var resp = await client.PostAsync(url, content);
            resp.EnsureSuccessStatusCode();
            var text = await resp.Content.ReadAsStringAsync();
            return JsonConvert.DeserializeObject<PredictionResult>(text) 
                   ?? throw new InvalidOperationException("La deserialización devolvió un valor nulo.");
        }

        // lee CSV de una sola fila y envía JSON al endpoint de SHAP
        private async Task<Dictionary<string, double>> EnviarCsvYObtenerShapAsync(string filePath, string url)
        {
            var (headers, values) = LeerCabeceraYValores(filePath);
            var payload = ConstruirPayload(headers, values);

            using var client = new HttpClient();
            var json = JsonConvert.SerializeObject(payload);
            var content = new StringContent(json, Encoding.UTF8, "application/json");
            var resp = await client.PostAsync(url, content);
            resp.EnsureSuccessStatusCode();
            var text = await resp.Content.ReadAsStringAsync();
            return JsonConvert.DeserializeObject<Dictionary<string, double>>(text) 
                   ?? new Dictionary<string, double>();
        }

        // helper: devuelve cabecera y la única línea de datos
        private (string[] headers, string[] values) LeerCabeceraYValores(string path)
        {
            var lines = File.ReadAllLines(path);
            if (lines.Length < 2)
                throw new InvalidOperationException("el CSV debe tener al menos dos líneas");
            var headers = lines[0].Split(',').Select(h => h.Trim()).ToArray();
            var values = lines[1].Split(',').Select(v => v.Trim()).ToArray();
            return (headers, values);
        }

        // helper: crea el diccionario JSON esperado por la API
        private Dictionary<string, object> ConstruirPayload(string[] headers, string[] values)
        {
            var dict = new Dictionary<string, object>();
            for (int i = 0; i < headers.Length && i < values.Length; i++)
                dict[headers[i]] = values[i];
            return dict;
        }
    }

    public class ColumnDescription
    {
        public string Column { get; set; } = string.Empty;
        public string Description { get; set; } = string.Empty;
    }

    public class PredictionResult
    {
        public int prediction { get; set; }
        public double probability { get; set; }
    }
}
