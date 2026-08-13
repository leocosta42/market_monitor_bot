import os
import plotly.graph_objects as go
import numpy as np
from datetime import datetime

class ChartGenerator:
    """
    Gera gráficos modernos em modo escuro (Dark Mode) para uso em alertas do Telegram/Discord.
    """
    
    # Paleta de Cores Moderna (Dark Theme)
    BG_COLOR = "#121214"
    PAPER_COLOR = "#1A1D24"
    GRID_COLOR = "rgba(255, 255, 255, 0.1)"
    TEXT_COLOR = "#E1E1E6"
    
    COLOR_UP = "#00E676"  # Verde de alta
    COLOR_DOWN = "#FF5252" # Vermelho de baixa
    COLOR_TREND = "#00B0FF" # Azul cyan para tendência/pressão
    
    @classmethod
    def generate_pressure_chart(cls, match_title: str, current_pressure: float, rsi_value: float = None, output_path: str = "chart.png"):
        """
        Gera um gráfico simulado de pressão/momentum com base nas especificações modernas.
        Como não temos histórico real na v1, geramos uma curva estilizada que culmina na pressão atual.
        """
        # Simulando dados de tempo (ex: 0 a 45 minutos) e uma curva de pressão que leva ao valor atual
        times = np.arange(0, 46, 1)
        
        # Gerando uma curva sintética (random walk com viés para o valor atual no final)
        np.random.seed(hash(match_title) % (2**32))
        noise = np.random.normal(0, 5, len(times)).cumsum()
        
        # Ajusta a curva para terminar exatamente no `current_pressure`
        offset = current_pressure - noise[-1]
        y_values = noise + offset
        y_values = np.clip(y_values, 0, 100) # Mantém entre 0 e 100
        
        # Define se a tendência final é de alta (verde) ou baixa (vermelho)
        is_up = y_values[-1] > y_values[0]
        line_color = cls.COLOR_UP if is_up else cls.COLOR_DOWN
        fill_color = f"rgba({0},{230},{118},0.2)" if is_up else f"rgba({255},{82},{82},0.2)"

        fig = go.Figure()

        # 2. Preenchimento Gradiente Suave
        fig.add_trace(go.Scatter(
            x=times, 
            y=y_values,
            mode='lines',
            line=dict(color=line_color, width=3),
            fill='tozeroy',
            fillcolor=fill_color, # Idealmente Plotly não suporta gradiente linear nativo fácil via Scatter, mas o fill semi-transparente cria um ótimo efeito
            name='Pressão'
        ))

        # Marcador no ponto final
        fig.add_trace(go.Scatter(
            x=[times[-1]],
            y=[y_values[-1]],
            mode='markers+text',
            marker=dict(color=line_color, size=10),
            text=[f"{y_values[-1]:.0f}"],
            textposition="top left",
            textfont=dict(color=line_color, size=14, weight="bold"),
            showlegend=False
        ))

        # 3. Hierarquia Visual no Card de Resumo & 4. Remoção de Ruído
        fig.update_layout(
            plot_bgcolor=cls.BG_COLOR,
            paper_bgcolor=cls.PAPER_COLOR,
            font=dict(family="Inter, Roboto, sans-serif", color=cls.TEXT_COLOR),
            title=dict(
                text=f"<b>{match_title.upper()}</b><br><sup>Pressão Atual: {current_pressure:.1f}</sup>",
                font=dict(size=24, color="#FFFFFF"),
                x=0.05,
                y=0.9
            ),
            margin=dict(l=40, r=40, t=100, b=40),
            xaxis=dict(
                showgrid=True, 
                gridcolor=cls.GRID_COLOR, 
                gridwidth=1, 
                griddash='dot',
                showline=False, # Remove borda inferior
                zeroline=False,
                title="Minutos"
            ),
            yaxis=dict(
                showgrid=True, 
                gridcolor=cls.GRID_COLOR, 
                gridwidth=1, 
                griddash='dot',
                showline=False, # Remove borda esquerda
                zeroline=False,
                side='right' # Coloca eixo Y na direita para não conflitar com o title
            ),
            showlegend=False,
            # Watermark discreto
            annotations=[
                dict(
                    x=0.5, y=0.5, xref="paper", yref="paper",
                    text="🤖 MARKET MONITOR BOT",
                    font=dict(size=30, color="rgba(255,255,255,0.05)", weight="bold"),
                    showarrow=False,
                    textangle=-30
                )
            ]
        )
        
        # 5. Indicadores com Códigos de Cores e Ícones (Adiciona Badges)
        if rsi_value is not None:
            rsi_color = cls.COLOR_UP if rsi_value < 30 else (cls.COLOR_DOWN if rsi_value > 70 else "#FFA000")
            rsi_text = f"🟢 RSI: {rsi_value} (Sobrevendido)" if rsi_value < 30 else (f"🔴 RSI: {rsi_value} (Sobrecomprado)" if rsi_value > 70 else f"🟡 RSI: {rsi_value} (Neutro)")
            
            fig.add_annotation(
                x=0.05, y=1.05, xref="paper", yref="paper",
                text=rsi_text,
                showarrow=False,
                font=dict(color=rsi_color, size=12),
                bgcolor="rgba(0,0,0,0.5)",
                bordercolor=rsi_color,
                borderwidth=1,
                borderpad=4
            )

        # Exportar imagem
        # Necessita: pip install -U kaleido
        fig.write_image(output_path, scale=2)
        return output_path

if __name__ == "__main__":
    # Teste rápido
    ChartGenerator.generate_pressure_chart(
        match_title="FLA vs FLU",
        current_pressure=85.4,
        rsi_value=75,
        output_path="test_chart.png"
    )
    print("Gráfico de teste gerado em test_chart.png!")
