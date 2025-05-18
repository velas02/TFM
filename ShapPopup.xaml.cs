// ShapPopup.xaml.cs
using LiveChartsCore;                        // ISeries, RowSeries<T>
using LiveChartsCore.Drawing;
using LiveChartsCore.Measure;                // Padding, Margin, AxisPosition
using LiveChartsCore.SkiaSharpView;          // RowSeries<T>
using LiveChartsCore.SkiaSharpView.Painting; // SolidColorPaint
using LiveChartsCore.SkiaSharpView.WPF;      // CartesianChart
using SkiaSharp;                             // SKPaint, SKColors
using System;
using System.Collections.Generic;
using System.Linq;
using System.Windows;

namespace TFMUI
{
    public partial class ShapPopup : Window
    {
        public ISeries[] Series { get; set; }
        public Axis[] XAxes { get; set; }
        public Axis[] YAxes { get; set; }

        public ShapPopup()
        {
            InitializeComponent();
        }

        public ShapPopup(
            double expected,
            double shapSum,
            double predicted,
            IDictionary<string, double> shapValues
        )
        {
            InitializeComponent();

            // 1) filtrar valores ≠ 0 y ordenar por contribución absoluta
            var items = shapValues
                .Where(kv => Math.Abs(kv.Value) > 1e-9)
                .Select(kv => new
                {
                    Name = kv.Key,
                    Value = kv.Value * 100   // convertir a puntos porcentuales
                })
                .OrderByDescending(x => Math.Abs(x.Value))
                .ToList();

            // 2) medir ancho máximo de etiqueta del eje Y
            using var paintY = new SKPaint { TextSize = 12f };
            var maxLabelWidth = items
                .Select(x => paintY.MeasureText(x.Name))
                .DefaultIfEmpty(0)
                .Max();

            // 3) medir altura de las etiquetas del eje X (valores numéricos)
            using var paintX = new SKPaint { TextSize = 12f };
            var fmX = paintX.FontMetrics;
            var xLabelHeight = (int)(Math.Abs(fmX.Ascent) + Math.Abs(fmX.Descent));

            // 4) medir altura del texto del nombre del eje X
            var xName = "Contribución SHAP (p.p.)";
            var xNameHeight = (int)(Math.Abs(fmX.Ascent) + Math.Abs(fmX.Descent));

            // 5) reservar espacio dinámico en DrawMargin
            ChartShap.DrawMargin = new Margin(
                left: (int)maxLabelWidth + 40,               // espacio para labels Y
                top: 10,
                right: 10,
                bottom: xLabelHeight + xNameHeight + 30        // etiquetas + nombre + padding extra
            );

            // 6) ajustar la altura según número de elementos
            ChartShap.Height = items.Count * 30 + 50;

            // 7) texto resumen: base, ΔSHAP y predicción
            var basePct = expected * 100;
            var deltaPct = shapSum * 100;
            var predPct = predicted * 100;
            TxtResumen.Text =
                $"Probabilidad Base: {basePct:F1}%  →  " +
                $"Δ SHAP: {deltaPct:+0.0;-0.0} p.p.  →  " +
                $"Predicción: {predPct:F1}%";

            // 8) serie de barras horizontales
            Series = new ISeries[]
            {
                new RowSeries<double>
                {
                    Values             = items.Select(x => x.Value).ToArray(),
                    DataLabelsPaint    = new SolidColorPaint(SKColors.Black),
                    DataLabelsSize     = 12,
                    DataLabelsPosition = DataLabelsPosition.Middle,
                    MaxBarWidth        = 20
                }
            };

            // 9) eje Y sin padding extra
            YAxes = new[]
            {
                new Axis
                {
                    Labels   = items.Select(x => x.Name).ToArray(),
                    TextSize = 12,
                    Padding  = new Padding(0)
                }
            };

            // 10) eje X en la parte inferior del DrawMargin
            XAxes = new[]
            {
                new Axis
                {
                    Name      = xName,
                    Labeler   = v => $"{v:+0.0;-0.0}",
                    TextSize  = 12,
                    Position  = AxisPosition.Start,      // <--- obliga a dibujar el eje X por debajo
                    NameTextSize = 12,
                    NamePaint    = new SolidColorPaint(SKColors.Black),
                    NamePadding  = new Padding(0, 10, 0, 0) // separa nombre de las etiquetas
                }
            };

            // 11) DataContext para binding
            DataContext = this;
        }
    }
}
