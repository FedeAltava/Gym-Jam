import type { ExerciseGuide } from './types';

// Free Exercise DB (public domain): level and muscles as published;
// steps translated to Spanish and condensed from its instructions.
export const SHOULDERS_GUIDES: Record<string, ExerciseGuide> = {
  'Arnold_Dumbbell_Press': {
    level: 'intermediate',
    primaryMuscles: ['shoulders'],
    secondaryMuscles: ['triceps'],
    steps: [
      'Siéntate en un banco con respaldo y sujeta dos mancuernas delante de ti a la altura de la parte alta del pecho, con las palmas hacia el cuerpo y los codos flexionados.',
      'Los brazos quedan pegados al tronco, como en la parte final de un curl de bíceps: es la posición inicial.',
      'Sube las mancuernas girando las palmas hasta que miren al frente y sigue hasta estirar los brazos por encima de la cabeza, mientras espiras.',
      'Tras un segundo de pausa arriba, baja girando las palmas de nuevo hacia ti mientras inspiras.',
    ],
  },
  'Front_Cable_Raise': {
    level: 'beginner',
    primaryMuscles: ['shoulders'],
    secondaryMuscles: [],
    steps: [
      'Elige el peso en una polea baja y sujeta el asa individual con la mano izquierda.',
      'Ponte de espaldas a la polea con el brazo estirado y el asa delante del muslo, con la palma mirando hacia él: es la posición inicial.',
      'Sin balancear el tronco, sube el brazo al frente con el codo ligeramente flexionado y la palma hacia abajo, hasta algo por encima de la horizontal.',
      'Espira al subir y haz una pausa de un segundo arriba.',
      'Baja despacio mientras inspiras y, al acabar las repeticiones, cambia de brazo.',
    ],
  },
  'Dumbbell_Shoulder_Press': {
    level: 'intermediate',
    primaryMuscles: ['shoulders'],
    secondaryMuscles: ['triceps'],
    steps: [
      'Siéntate en un banco con respaldo con una mancuerna en cada mano apoyada en vertical sobre los muslos.',
      'Ayúdate de los muslos para subir las mancuernas de una en una hasta la altura de los hombros.',
      'Gira las muñecas para que las palmas miren al frente: es la posición inicial.',
      'Espira y empuja las mancuernas hacia arriba hasta que se toquen en lo alto.',
      'Tras una breve pausa arriba, baja despacio a la posición inicial mientras inspiras.',
    ],
  },
  'Face_Pull': {
    level: 'intermediate',
    primaryMuscles: ['shoulders'],
    secondaryMuscles: ['middle back'],
    steps: [
      'Colócate de cara a una polea alta con una cuerda o dos asas y sujétala con ambas manos.',
      'Tira del peso directamente hacia la cara, separando las manos a medida que se acerca.',
      'Mantén los brazos paralelos al suelo durante todo el movimiento.',
      'Vuelve a la posición inicial con control y repite.',
    ],
  },
  'Front_Dumbbell_Raise': {
    level: 'beginner',
    primaryMuscles: ['shoulders'],
    secondaryMuscles: [],
    steps: [
      'De pie, con el tronco recto, sujeta una mancuerna en cada mano delante de los muslos, con los brazos estirados y las palmas mirando hacia ellos: es la posición inicial.',
      'Sin balancear el tronco, sube la mancuerna izquierda al frente con el codo ligeramente flexionado y la palma hacia abajo, hasta algo por encima de la horizontal.',
      'Espira al subir, haz una pausa de un segundo arriba e inspira.',
      'Baja la mancuerna despacio mientras subes la derecha, y sigue alternando hasta completar las repeticiones con cada brazo.',
    ],
  },
  'Side_Lateral_Raise': {
    level: 'beginner',
    primaryMuscles: ['shoulders'],
    secondaryMuscles: [],
    steps: [
      'De pie, con el tronco recto, sujeta una mancuerna en cada mano a los lados del cuerpo, con los brazos estirados y las palmas hacia ti: es la posición inicial.',
      'Sin balancear el tronco, sube las mancuernas a los lados con los codos ligeramente flexionados y las manos un poco inclinadas hacia delante, como si vertieras agua en un vaso.',
      'Sube hasta que los brazos queden paralelos al suelo, espirando, y haz una pausa de un segundo arriba.',
      'Baja las mancuernas despacio a la posición inicial mientras inspiras.',
    ],
  },
  'Seated_Bent-Over_Rear_Delt_Raise': {
    level: 'intermediate',
    primaryMuscles: ['shoulders'],
    secondaryMuscles: [],
    steps: [
      'Deja un par de mancuernas delante de un banco plano y siéntate en el borde con las piernas juntas y las mancuernas detrás de las pantorrillas.',
      'Inclínate desde la cadera con la espalda recta y coge las mancuernas con las palmas enfrentadas: es la posición inicial.',
      'Con el tronco inclinado y quieto y los codos ligeramente flexionados, sube las mancuernas a los lados hasta que los brazos queden paralelos al suelo, espirando.',
      'No balancees el tronco ni lleves los brazos hacia atrás en lugar de hacia los lados.',
      'Tras un segundo de contracción arriba, baja despacio a la posición inicial.',
    ],
  },
  'Reverse_Machine_Flyes': {
    level: 'beginner',
    primaryMuscles: ['shoulders'],
    secondaryMuscles: [],
    steps: [
      'Ajusta las asas en la posición más atrasada, elige el peso y regula el asiento para que las asas queden a la altura de los hombros.',
      'Agarra las asas con las palmas enfrentadas: es la posición inicial.',
      'Lleva las manos hacia los lados y hacia atrás en un movimiento semicircular, contrayendo los deltoides posteriores.',
      'Mantén los brazos ligeramente flexionados: todo el movimiento sale de la articulación del hombro.',
      'Haz una pausa al final del recorrido y vuelve despacio a la posición inicial.',
    ],
  },
  'Machine_Shoulder_Military_Press': {
    level: 'beginner',
    primaryMuscles: ['shoulders'],
    secondaryMuscles: ['triceps'],
    steps: [
      'Siéntate en la máquina de press de hombros y elige el peso.',
      'Agarra las asas a los lados con los codos flexionados y alineados con el tronco: es la posición inicial.',
      'Empuja las asas hacia arriba mientras espiras hasta estirar del todo los brazos, y aguanta la contracción un segundo.',
      'Baja las asas despacio a la posición inicial mientras inspiras.',
    ],
  },
  'Dumbbell_Shrug': {
    level: 'beginner',
    primaryMuscles: ['traps'],
    secondaryMuscles: [],
    steps: [
      'De pie, erguido, con una mancuerna en cada mano a los lados y las palmas hacia el tronco, con los brazos estirados.',
      'Sube las mancuernas elevando los hombros todo lo que puedas mientras espiras, y aguanta la contracción un segundo arriba.',
      'Mantén los brazos estirados todo el tiempo y no ayudes con los bíceps: solo los hombros suben y bajan.',
      'Baja las mancuernas a la posición inicial.',
    ],
  },
  'Upright_Barbell_Row': {
    level: 'beginner',
    primaryMuscles: ['shoulders'],
    secondaryMuscles: ['traps'],
    steps: [
      'Agarra la barra con agarre prono, algo más estrecho que la anchura de los hombros, y déjala apoyada en los muslos con los brazos casi estirados y la espalda recta.',
      'Espira y sube la barra pegada al cuerpo tirando con los hombros, llevando los codos hacia arriba y hacia fuera, hasta casi tocar la barbilla.',
      'Los codos guían el movimiento y van siempre más altos que los antebrazos; mantén el tronco quieto y haz una pausa de un segundo arriba.',
      'Baja la barra despacio a la posición inicial mientras inspiras.',
    ],
  },
  'Leverage_Shoulder_Press': {
    level: 'beginner',
    primaryMuscles: ['shoulders'],
    secondaryMuscles: ['triceps'],
    steps: [
      'Elige el peso y ajusta el asiento a tu altura, de modo que las asas queden a la altura de los hombros al empezar.',
      'Mantén el pecho y la cabeza erguidos y agarra las asas con agarre prono: es la posición inicial.',
      'Empuja las asas hacia arriba extendiendo los codos.',
      'Tras una breve pausa arriba, vuelve hasta justo por encima de la posición inicial, sin apoyar el peso en los topes hasta terminar la serie.',
    ],
  },
};
