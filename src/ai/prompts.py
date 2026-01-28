"""
Prompt templates for Multi-Technical-Alerts.

Contains system prompt, few-shot examples, and prompt generation for OpenAI.
"""

import pandas as pd
from typing import List, Dict


# System prompt defining AI role and constraints
SYSTEM_PROMPT = """Eres un ingeniero mecánico, especialista en equipos mineros y debes realizar diagnósticos precisos sobre las medidas de un equipo, entregando comentarios breves respecto a los análisis de aceite realizados y recomendaciones concretas de mantención. Considera que al haber presencia de Zinc, Bario, Boro, Calcio, Molibdeno, Magnesio o Fósforo en el aceite no se debe sugerir cambio de componentes o de aceite. Tus respuestas deben ser de 150 palabras o menos."""


# Few-shot examples (3 mechanical engineering scenarios)
FEW_SHOT_EXAMPLES: List[Dict[str, str]] = [
    {
        "role": "user",
        "content": """Analiza una muestra para el siguiente equipo:
Componente: Aceite motor Diesel 15W40
Los valores de la muestra son:
                    elemento  valor          limite transgredido  valor limite
           Contenido de agua    8.3 limite superior condenatorio           0.3
Viscosidad cinemática @ 40°C  144.6 limite superior condenatorio         138.0"""
    },
    {
        "role": "assistant",
        "content": """Se aprecian niveles de desgaste y contaminación externa entre límites permisibles, sin embargo, se detecta contenido de agua 8,3% en volumen de muestra. Grado de viscosidad sobre límite superior condenatorio 144,6 por posibles rellenos con lubricante de ISO VG mayor.
Se sugiere cambio de lubricante y mantener seguimiento riguroso cada 125 horas, para evidenciar alzas abruptas de sodio y potasio por eventual traspaso de refrigerante. Monitorear consumos de aceite y gases blancos en salida de escape."""
    },
    {
        "role": "user",
        "content": """Analiza una muestra para el siguiente equipo:
Componente: Motor Diesel
Máquina: Camión Tolva
Los valores de la muestra son:
                     elemento  valor          limite transgredido  valor limite
                       Fierro   31.1     limite superior marginal          30.0
                        Cobre  267.7 limite superior condenatorio          15.0
                       Estaño    2.9     limite superior marginal           1.5
                      Silicio   30.7 limite superior condenatorio          17.0
                    Índice PQ   20.0     limite superior marginal          20.0
Viscosidad cinemática @ 100°C   10.7 limite inferior condenatorio          11.0
     Dilución por combustible    0.8 limite superior condenatorio           0.5"""
    },
    {
        "role": "assistant",
        "content": """Se detecta concentración de metales de desgaste por Fierro 31.1 ppm y Cobre 267.7 ppm, evidenciando posible abrasión excesiva en cojinetes y bujes de turbo. Silicio 30.7 ppm señala ingesta excesiva de polvo ambiental. Análisis fisicoquímico detecta material ferroso en suspensión Índice PQ 20.0. Se evidencia Dilución por combustible de 0.8%, detectando posible anormalidad en bomba de transferencia o sellos de inyectores, provocando una baja ligera en viscosidad en lubricante.
Se recomienda priorizar cambio de lubricante y elementos filtrantes, evaluar presiones en sistema de lubricación y saturación temprana de filtros, mantener seguimiento riguroso cada 50 hrs."""
    },
    {
        "role": "user",
        "content": """Analiza una muestra para el siguiente equipo:
Componente: Motor Diesel Cummins
Máquina: Camión Komatsu 730-E de Extracción
Los valores de la muestra son:
                elemento  valor          limite transgredido  valor limite
Dilución por combustible    2.2 limite superior condenatorio           0.3"""
    },
    {
        "role": "assistant",
        "content": """Niveles de desgaste y contaminaciones determinadas por espectrometría en tamaño y concentraciones admisibles para la operación, sin embargo, análisis físico químico detecta Dilución por combustible 2.2%, altamente perjudicial para la operación, evidenciando posibles anomalías en toberas o sellos de inyectores. Grado de visosidad normal en lubricante.
Se sugiere priorizar intervención mecánica y efectuar cambio de lubricante, junto con envío de contramuestra para realizar seguimiento a deterioro en sellos/toberas de inyectores o bomba de transferencia. Evaluar presiones en sistema de lubricación y saturación temprana de filtros."""
    }
]


def create_analysis_prompt(
    sample: pd.Series,
    breached_essays: pd.DataFrame
) -> str:
    """
    Create analysis prompt for a specific oil sample.
    
    Args:
        sample: Series with sample data (must include componentName, machineName, machineModel)
        breached_essays: DataFrame with essays that exceeded thresholds
    
    Returns:
        Formatted prompt string
    """
    component = sample.get('componentName', 'N/A')
    machine = sample.get('machineName', 'N/A')
    machine_model = sample.get('machineModel', 'N/A')
    
    # Format breached essays table
    essays_table = ""
    if not breached_essays.empty:
        # Create a formatted string representation
        essays_table = breached_essays[['essay', 'value', 'threshold', 'limit']].to_string(index=False)
    else:
        essays_table = "No hay ensayos fuera de límite"
    
    prompt = f"""Analiza una muestra para el siguiente equipo:
Componente: {component.lower() if isinstance(component, str) else component}
Máquina: {machine.lower() if isinstance(machine, str) else machine} - {machine_model.upper() if isinstance(machine_model, str) else machine_model}

Los valores de la muestra son:
{essays_table}"""
    
    return prompt


def create_full_messages(
    sample: pd.Series,
    breached_essays: pd.DataFrame
) -> List[Dict[str, str]]:
    """
    Create full message list for OpenAI Chat API.
    
    Includes system prompt, few-shot examples, and user prompt.
    
    Args:
        sample: Sample data
        breached_essays: Breached essays DataFrame
    
    Returns:
        List of message dicts for OpenAI API
    """
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    
    # Add few-shot examples
    messages.extend(FEW_SHOT_EXAMPLES)
    
    # Add user prompt
    user_prompt = create_analysis_prompt(sample, breached_essays)
    messages.append({"role": "user", "content": user_prompt})
    
    return messages
