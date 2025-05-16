using System;
using System.Windows;
using System.Windows.Input;
using System.Windows.Media.Imaging;

namespace TFMUI
{
    public partial class PredictionPopup : Window
    {
        public PredictionPopup(int prediction, double probability)
        {
            InitializeComponent();

            // si clase éxito
            if (prediction == 1)
            {
                Icon.Source = new BitmapImage(
                    new Uri("C:\\Users\\David\\Desktop\\TFM\\TFMUI\\Resources\\success.png"));
                MessageText.Text = "La startup es un éxito";
                ConfidenceText.Text =
                    $"Confianza: {(int)(probability * 100)} %";
            }
            else // clase fracaso
            {
                Icon.Source = new BitmapImage(
                    new Uri("C:\\Users\\David\\Desktop\\TFM\\TFMUI\\Resources\\failure.png"));
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
