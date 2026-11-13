import type { ExerciseGuide } from './types';

// Free Exercise DB (public domain): level and muscles as published;
// steps translated to Spanish and condensed from its instructions.
export const CHEST_GUIDES: Record<string, ExerciseGuide> = {
  'Barbell_Bench_Press_-_Medium_Grip': {
    level: 'beginner',
    primaryMuscles: ['chest'],
    secondaryMuscles: ['shoulders', 'triceps'],
    steps: [
      'Túmbate en un banco plano y agarra la barra con un agarre medio, de modo que antebrazos y brazos formen 90° a mitad del recorrido.',
      'Saca la barra del soporte y sujétala recta sobre el pecho con los brazos estirados: es la posición inicial.',
      'Inspira y baja la barra despacio hasta tocar la parte media del pecho.',
      'Tras una breve pausa, empuja la barra con el pecho hasta arriba mientras espiras; estira los brazos y contrae el pecho un segundo.',
      'Baja el doble de lento de lo que subes y, al terminar, deja la barra en el soporte.',
    ],
  },
  'Cable_Crossover': {
    level: 'beginner',
    primaryMuscles: ['chest'],
    secondaryMuscles: ['shoulders'],
    steps: [
      'Coloca las poleas en posición alta, por encima de la cabeza, elige el peso y sujeta un asa en cada mano.',
      'Da un paso al frente, junta las manos delante de ti e inclina un poco el tronco hacia delante: es la posición inicial.',
      'Con los codos ligeramente flexionados, abre los brazos a los lados en un arco amplio mientras inspiras, hasta notar el estiramiento en el pecho.',
      'Mueve solo la articulación del hombro: los brazos y el tronco se mantienen fijos.',
      'Vuelve a juntar las manos siguiendo el mismo arco mientras espiras y aguanta un segundo.',
    ],
  },
  'Low_Cable_Crossover': {
    level: 'beginner',
    primaryMuscles: ['chest'],
    secondaryMuscles: ['shoulders'],
    steps: [
      'Coloca las poleas en posición baja, elige el peso y sujeta un asa en cada mano.',
      'Da un paso al frente para tensar los cables, con las palmas hacia delante, las manos por debajo de la cintura y los brazos estirados.',
      'Con los brazos ligeramente flexionados, sube las manos hacia arriba y hacia el centro hasta juntarlas delante del pecho, con las palmas hacia arriba.',
      'Tras una breve pausa, vuelve despacio a la posición inicial.',
    ],
  },
  'Dips_-_Chest_Version': {
    level: 'intermediate',
    primaryMuscles: ['chest'],
    secondaryMuscles: ['shoulders', 'triceps'],
    steps: [
      'Sujétate sobre las barras paralelas con los brazos estirados y bloqueados: es la posición inicial.',
      'Inspira y baja despacio con el tronco inclinado unos 30° hacia delante y los codos un poco abiertos, hasta notar un ligero estiramiento en el pecho.',
      'Cuando notes el estiramiento, empuja con el pecho para volver arriba mientras espiras.',
      'Contrae el pecho un segundo en la parte alta y repite.',
    ],
  },
  'Butterfly': {
    level: 'beginner',
    primaryMuscles: ['chest'],
    secondaryMuscles: [],
    steps: [
      'Siéntate en la máquina con la espalda bien apoyada en el respaldo.',
      'Agarra las asas y ajusta la máquina para que los brazos queden paralelos al suelo: es la posición inicial.',
      'Junta las asas despacio contrayendo el pecho en el centro mientras espiras, y aguanta la contracción un segundo.',
      'Vuelve despacio a la posición inicial mientras inspiras, hasta notar el pecho totalmente estirado.',
    ],
  },
  'Machine_Bench_Press': {
    level: 'beginner',
    primaryMuscles: ['chest'],
    secondaryMuscles: ['shoulders', 'triceps'],
    steps: [
      'Siéntate en la máquina de press de pecho y elige el peso.',
      'Si la máquina tiene palanca de pie, písala para adelantar las asas; agárralas con las palmas hacia abajo y estira los brazos.',
      'Sube los codos hasta que los brazos queden paralelos al suelo, a los lados del tronco: es la posición inicial.',
      'Acerca las asas hacia ti mientras inspiras.',
      'Empuja las asas hacia delante contrayendo el pecho mientras espiras, y aguanta la contracción un segundo.',
      'Al terminar, devuelve las asas despacio a su sitio (con la palanca de pie, si la tiene).',
    ],
  },
  'Decline_Barbell_Bench_Press': {
    level: 'beginner',
    primaryMuscles: ['chest'],
    secondaryMuscles: ['shoulders', 'triceps'],
    steps: [
      'Fija las piernas en el extremo del banco declinado y túmbate despacio.',
      'Con un agarre medio, saca la barra del soporte y sujétala sobre ti con los brazos estirados, perpendiculares al suelo: es la posición inicial.',
      'Para proteger el manguito rotador, mejor que alguien te ayude a sacar la barra del soporte.',
      'Inspira y baja la barra despacio hasta notarla en la parte baja del pecho.',
      'Tras una pausa de un segundo, empuja con el pecho hasta arriba mientras espiras; bloquea los brazos y contrae el pecho un segundo.',
      'Baja al menos el doble de lento de lo que subes y, al terminar, deja la barra en el soporte.',
    ],
  },
  'Dumbbell_Bench_Press': {
    level: 'beginner',
    primaryMuscles: ['chest'],
    secondaryMuscles: ['shoulders', 'triceps'],
    steps: [
      'Túmbate en un banco plano con una mancuerna en cada mano apoyada sobre los muslos, con las palmas enfrentadas.',
      'Ayúdate de los muslos para subir las mancuernas de una en una y sujetarlas delante de ti a la anchura de los hombros.',
      'Gira las muñecas para que las palmas miren al frente, con las mancuernas a los lados del pecho y los codos a 90°: es la posición inicial.',
      'Espira y empuja las mancuernas hacia arriba con el pecho; bloquea los brazos arriba, contrae el pecho y aguanta un segundo.',
      'Baja despacio, idealmente el doble de lento de lo que subes, manteniendo siempre el control de las mancuernas.',
    ],
  },
  'Dumbbell_Flyes': {
    level: 'beginner',
    primaryMuscles: ['chest'],
    secondaryMuscles: [],
    steps: [
      'Túmbate en un banco plano con una mancuerna en cada mano sobre los muslos, con las palmas enfrentadas.',
      'Ayúdate de los muslos para subir las mancuernas de una en una y sujétalas sobre el pecho, con las palmas enfrentadas, sin llegar a bloquear los codos.',
      'Con los codos ligeramente flexionados, abre los brazos a los lados en un arco amplio mientras inspiras, hasta notar el estiramiento en el pecho.',
      'Mantén los brazos fijos: el movimiento sale solo de la articulación del hombro.',
      'Vuelve por el mismo arco contrayendo el pecho mientras espiras, y aguanta un segundo arriba.',
    ],
  },
  'Barbell_Incline_Bench_Press_-_Medium_Grip': {
    level: 'beginner',
    primaryMuscles: ['chest'],
    secondaryMuscles: ['shoulders', 'triceps'],
    steps: [
      'Túmbate en un banco inclinado y agarra la barra con un agarre medio, de modo que antebrazos y brazos formen 90° a mitad del recorrido.',
      'Saca la barra del soporte y sujétala recta sobre ti con los brazos estirados: es la posición inicial.',
      'Inspira y baja la barra despacio hasta notarla en la parte alta del pecho.',
      'Tras una pausa de un segundo, empuja con el pecho hasta arriba mientras espiras; bloquea los brazos y contrae el pecho un segundo.',
      'Baja al menos el doble de lento de lo que subes y, al terminar, deja la barra en el soporte.',
    ],
  },
  'Incline_Dumbbell_Press': {
    level: 'beginner',
    primaryMuscles: ['chest'],
    secondaryMuscles: ['shoulders', 'triceps'],
    steps: [
      'Túmbate en un banco inclinado con una mancuerna en cada mano sobre los muslos, con las palmas enfrentadas.',
      'Ayúdate de los muslos para subir las mancuernas de una en una hasta la altura de los hombros.',
      'Gira las muñecas para que las palmas miren al frente: es la posición inicial.',
      'Espira y empuja las mancuernas hacia arriba con el pecho; bloquea los brazos arriba y aguanta un segundo.',
      'Baja despacio y con control, idealmente el doble de lento de lo que subes.',
      'Al terminar, apoya las mancuernas en los muslos y después en el suelo: es la forma más segura de soltarlas.',
    ],
  },
  'Leverage_Incline_Chest_Press': {
    level: 'beginner',
    primaryMuscles: ['chest'],
    secondaryMuscles: ['shoulders', 'triceps'],
    steps: [
      'Elige el peso y ajusta el asiento a tu altura, de modo que las asas queden a la altura de la parte alta del pecho al empezar.',
      'Mantén el pecho y la cabeza erguidos y las escápulas retraídas: es la posición inicial.',
      'Empuja las asas hacia delante extendiendo los codos.',
      'Tras una breve pausa arriba, vuelve hasta justo por encima de la posición inicial, sin apoyar el peso en los topes hasta terminar la serie.',
    ],
  },
  'Pushups': {
    level: 'beginner',
    primaryMuscles: ['chest'],
    secondaryMuscles: ['shoulders', 'triceps'],
    steps: [
      'Túmbate boca abajo con las manos apoyadas en el suelo, separadas unos 90 cm, y sujeta el tronco con los brazos estirados.',
      'Inspira y baja hasta que el pecho casi toque el suelo.',
      'Espira y empuja para volver arriba contrayendo el pecho.',
      'Haz una breve pausa arriba y vuelve a bajar.',
    ],
  },
  'Leverage_Chest_Press': {
    level: 'beginner',
    primaryMuscles: ['chest'],
    secondaryMuscles: ['shoulders', 'triceps'],
    steps: [
      'Elige el peso y ajusta el asiento a tu altura, de modo que las asas queden a la altura de la parte media o baja del pecho al empezar.',
      'Mantén el pecho y la cabeza erguidos y las escápulas retraídas: es la posición inicial.',
      'Empuja las asas hacia delante extendiendo los codos.',
      'Tras una breve pausa arriba, vuelve hasta justo por encima de la posición inicial, sin apoyar el peso en los topes hasta terminar la serie.',
    ],
  },
  'Leverage_Decline_Chest_Press': {
    level: 'beginner',
    primaryMuscles: ['chest'],
    secondaryMuscles: ['shoulders', 'triceps'],
    steps: [
      'Elige el peso y ajusta el asiento a tu altura, de modo que las asas queden a la altura de la parte baja del pecho al empezar.',
      'Mantén el pecho y la cabeza erguidos y las escápulas retraídas: es la posición inicial.',
      'Empuja las asas hacia delante extendiendo los codos.',
      'Tras una breve pausa arriba, vuelve hasta justo por encima de la posición inicial, sin apoyar el peso en los topes hasta terminar la serie.',
    ],
  },
};
