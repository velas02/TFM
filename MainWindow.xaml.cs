using Microsoft.Win32;
using Newtonsoft.Json;
using Newtonsoft.Json.Linq;
using System;
using System.Collections.ObjectModel;
using System.IO;
using System.Linq;
using System.Net.Http;
using System.Threading.Tasks;
using System.Windows;
using System.Windows.Input;

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
                new ColumnDescription { Column = "funding_total_usd", Description = "Financiación total en USD" },
                new ColumnDescription { Column = "milestones", Description = "Número de hitos" },
                new ColumnDescription { Column = "state_code.1", Description = "Código del estado (duplicado)" },
                new ColumnDescription { Column = "is_CA", Description = "Indica si está en California" },
                new ColumnDescription { Column = "is_NY", Description = "Indica si está en Nueva York" },
                new ColumnDescription { Column = "is_MA", Description = "Indica si está en Massachusetts" },
                new ColumnDescription { Column = "is_TX", Description = "Indica si está en Texas" },
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
                new ColumnDescription { Column = "has_roundA", Description = "Ha recibido financiación en ronda A" },
                new ColumnDescription { Column = "has_roundB", Description = "Ha recibido financiación en ronda B" },
                new ColumnDescription { Column = "has_roundC", Description = "Ha recibido financiación en ronda C" },
                new ColumnDescription { Column = "has_roundD", Description = "Ha recibido financiación en ronda D" },
                new ColumnDescription { Column = "avg_participants", Description = "Promedio de participantes por ronda" },
                new ColumnDescription { Column = "is_top500", Description = "Indica si está en el top 500" },
                new ColumnDescription { Column = "status", Description = "Estado actual de la empresa" }
            };
            dataGrid.ItemsSource = _sampleData;
        }

        private void CsvDropZone_DragOver(object sender, DragEventArgs e)
        {
            e.Handled = true;
            e.Effects = e.Data.GetDataPresent(DataFormats.FileDrop) &&
                        ((string[])e.Data.GetData(DataFormats.FileDrop))
                         .First().EndsWith(".csv", StringComparison.OrdinalIgnoreCase)
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
                Title = "Seleccionar archivo CSV"
            };
            if (dlg.ShowDialog() == true)
            {
                SetCsvFile(dlg.FileName);
            }
        }

        private void SetCsvFile(string path)
        {
            _csvFilePath = path;
            txtDropZone.Text = $"📄: {Path.GetFileName(path)}";
        }

        private async void PredictSvm_Click(object sender, RoutedEventArgs e)
        {
            if (string.IsNullOrEmpty(_csvFilePath))
            {
                MessageBox.Show("primero seleccione un archivo CSV",
                                "advertencia",
                                MessageBoxButton.OK,
                                MessageBoxImage.Warning);
                return;
            }

            var result = await EnviarCsvYObtenerPrediccionAsync(
                              _csvFilePath,
                              "http://localhost:5000/predict_svm");

            var popup = new PredictionPopup(
                "svm",
                result.prediction,
                result.probability);
            popup.Owner = this;
            popup.ShowDialog();

        }

        private async void PredictMlp_Click(object sender, RoutedEventArgs e)
        {
            if (string.IsNullOrEmpty(_csvFilePath))
            {
                MessageBox.Show("primero seleccione un archivo CSV",
                                "advertencia",
                                MessageBoxButton.OK,
                                MessageBoxImage.Warning);
                return;
            }

            var result = await EnviarCsvYObtenerPrediccionAsync(_csvFilePath,
                                      "http://localhost:5000/predict_mlp");

            // usa el mismo popup que para SVM
            var popup = new PredictionPopup(
                "mlp",
                result.prediction,
                result.probability);
            popup.Owner = this;
            popup.ShowDialog();
        }

        private async void ShapSvm_Click(object sender, RoutedEventArgs e)
        {
            if (string.IsNullOrEmpty(_csvFilePath))
            {
                MessageBox.Show("primero seleccione un archivo CSV",
                                "advertencia",
                                MessageBoxButton.OK,
                                MessageBoxImage.Warning);
                return;
            }

            var (expected, shapSum, predicted, shapDict) =
                await EnviarCsvYObtenerShapAsync(_csvFilePath,
                                                "http://localhost:5000/explain_svm");

            var popup = new ShapPopup(expected,
                                      shapSum,
                                      predicted,
                                      shapDict);
            popup.Owner = this;
            popup.ShowDialog();
        }


        private async void ShapMlp_Click(object sender, RoutedEventArgs e)
        {
            if (string.IsNullOrEmpty(_csvFilePath))
            {
                MessageBox.Show("primero seleccione un archivo CSV",
                                "advertencia",
                                MessageBoxButton.OK,
                                MessageBoxImage.Warning);
                return;
            }

            var (expected, shapSum, predicted, shapValues) =
                await EnviarCsvYObtenerShapAsync(_csvFilePath,
                                                "http://localhost:5000/explain_mlp");

            // usa el mismo popup que para SVM
            var popup = new ShapPopup(
                expected,
                shapSum,
                predicted,
                shapValues);
            popup.Owner = this;
            popup.ShowDialog();
        }

        private async Task<PredictionResult> EnviarCsvYObtenerPrediccionAsync(string filePath, string url)
        {
            using var client = new HttpClient();
            using var stream = File.OpenRead(filePath);
            using var form = new MultipartFormDataContent
            {
                { new StreamContent(stream), "file", Path.GetFileName(filePath) }
            };

            var resp = await client.PostAsync(url, form);
            resp.EnsureSuccessStatusCode();
            var text = await resp.Content.ReadAsStringAsync();
            return JsonConvert.DeserializeObject<PredictionResult>(text)
                   ?? throw new InvalidOperationException("respuesta nula");
        }

        private async Task<(double expected, double shapSum, double predicted, Dictionary<string, double> shapValues)>
            EnviarCsvYObtenerShapAsync(string filePath, string url)
        {
            using var client = new HttpClient();
            using var stream = File.OpenRead(filePath);
            using var form = new MultipartFormDataContent
            {
                { new StreamContent(stream), "file", Path.GetFileName(filePath) }
            };

            var resp = await client.PostAsync(url, form);
            resp.EnsureSuccessStatusCode();
            var text = await resp.Content.ReadAsStringAsync();

            // parseamos el JSON completo
            var obj = JObject.Parse(text);

            // extraemos los valores escalares
            double expected = obj["expected_value"].Value<double>();
            double shapSum = obj["shap_sum"].Value<double>();
            double predicted = obj["predicted_probability"].Value<double>();

            // extraemos el diccionario de contribuciones
            var shapValues = obj["shap_values"]
                                .ToObject<Dictionary<string, double>>()
                            ?? new Dictionary<string, double>();

            return (expected, shapSum, predicted, shapValues);
        }


    }
}
