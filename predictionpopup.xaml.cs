using System;
using System.Windows;
using System.Windows.Input;
using System.Windows.Media.Imaging;

namespace TFMUI
{
    public partial class PredictionPopup : Window
    {
        /// <summary>
        /// Constructor del popup de predicción.
        /// </summary>
        /// <param name="modelType">"svm" o "mlp" (sin distinción de mayúsculas).</param>
        /// <param name="prediction">0 o 1, etiqueta predicha.</param>
        /// <param name="probability">probabilidad asociada a la clase 1.</param>
        public PredictionPopup(string modelType, int prediction, double probability)
        {
            InitializeComponent();

            // asignar título dinámico
            TitleText.Text = $"Predicción ({modelType.ToUpper()})";

            // seleccionar icono y mensaje según la etiqueta
            if (prediction == 1)
            {
                Icon.Source = new BitmapImage(
                    new Uri("C:\\Users\\David\\Desktop\\TFMUI\\Resources\\success.png"));
                MessageText.Text = "La startup es un éxito";
                ConfidenceText.Text =
                    $"Confianza: {(int)(probability * 100)} %";
            }
            else
            {
                Icon.Source = new BitmapImage(
                    new Uri("C:\\Users\\David\\Desktop\\TFMUI\\Resources\\failure.png"));
                MessageText.Text = "La startup es un fracaso";
                ConfidenceText.Text =
                    $"Confianza: {100 - (int)(probability * 100)} %";
            }
        }

        private void Close_Click(object sender, RoutedEventArgs e)
        {
            this.Close();
        }

        private void Window_MouseLeftButtonDown(object sender, MouseButtonEventArgs e)
        {
            DragMove();
        }
    }
}
