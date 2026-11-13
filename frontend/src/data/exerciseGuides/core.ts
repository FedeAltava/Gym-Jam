import type { ExerciseGuide } from './types';

// Free Exercise DB (public domain): level and muscles as published;
// steps translated to Spanish and condensed from its instructions.
export const CORE_GUIDES: Record<string, ExerciseGuide> = {
  'Ab_Roller': {
    level: 'intermediate',
    primaryMuscles: ['abdominals'],
    secondaryMuscles: ['shoulders'],
    steps: [
      'Arrodíllate en el suelo y sujeta la rueda con las dos manos, apoyándola delante de ti como en una posición de flexión de rodillas: es la posición inicial.',
      'Rueda despacio hacia delante estirando el cuerpo hasta quedar recto, mientras inspiras. Baja todo lo que puedas sin tocar el suelo con el cuerpo.',
      'Tras una pausa en el punto de máximo estiramiento, vuelve a la posición inicial tirando del cuerpo mientras espiras.',
      'Ve despacio y mantén el abdomen contraído en todo momento.',
    ],
  },
  'Air_Bike': {
    level: 'beginner',
    primaryMuscles: ['abdominals'],
    secondaryMuscles: [],
    steps: [
      'Túmbate boca arriba con la zona lumbar pegada al suelo y las manos a los lados de la cabeza, sin tirar del cuello. Eleva los hombros como en un crunch.',
      'Sube las rodillas hasta que los muslos queden verticales y las pantorrillas paralelas al suelo: es la posición inicial.',
      'Pedalea despacio: estira la pierna derecha mientras acercas la rodilla izquierda y lleva el codo derecho hacia ella, girando el torso mientras espiras.',
      'Vuelve a la posición inicial mientras inspiras.',
      'Repite hacia el otro lado, acercando el codo izquierdo a la rodilla derecha, y sigue alternando.',
    ],
  },
  'Cable_Crunch': {
    level: 'beginner',
    primaryMuscles: ['abdominals'],
    secondaryMuscles: [],
    steps: [
      'Arrodíllate bajo una polea alta con la cuerda y bájala hasta tener las manos junto a la cara.',
      'Flexiona un poco la cadera y deja que el peso extienda la zona lumbar: es la posición inicial.',
      'Con la cadera quieta, flexiona el tronco contrayendo el abdomen hasta llevar los codos hacia la mitad de los muslos, mientras espiras. Aguanta un segundo.',
      'Vuelve despacio a la posición inicial mientras inspiras, manteniendo tensión constante en el abdomen.',
      'No uses un peso tan alto que el trabajo lo acabe haciendo la zona lumbar.',
    ],
  },
  'Ab_Crunch_Machine': {
    level: 'intermediate',
    primaryMuscles: ['abdominals'],
    secondaryMuscles: [],
    steps: [
      'Elige una resistencia ligera, siéntate con los pies bajo las almohadillas y agarra los asideros de arriba, con los codos a 90° y los tríceps apoyados: es la posición inicial.',
      'Eleva las piernas a la vez que encoges el torso, mientras espiras.',
      'Hazlo lento y controlado: mueve el peso con el abdomen, con las piernas y los pies relajados.',
      'Tras una pausa de un segundo, vuelve despacio a la posición inicial mientras inspiras.',
    ],
  },
  'Dead_Bug': {
    level: 'beginner',
    primaryMuscles: ['abdominals'],
    secondaryMuscles: [],
    steps: [
      'Túmbate boca arriba con los brazos extendidos hacia el techo y sube pies, rodillas y caderas a 90°.',
      'Espira fuerte para bajar las costillas y pegar la zona lumbar al suelo, basculando la pelvis y apretando los glúteos. Mantenlo todo el ejercicio: es la posición inicial.',
      'Extiende una pierna estirando rodilla y cadera hasta dejarla justo por encima del suelo.',
      'No dejes que la zona lumbar se arquee ni que la pelvis se mueva: mantente firme.',
      'Vuelve a la posición inicial con esa pierna y repite con la otra, alternando hasta acabar la serie.',
    ],
  },
  'Hanging_Leg_Raise': {
    level: 'expert',
    primaryMuscles: ['abdominals'],
    secondaryMuscles: [],
    steps: [
      'Cuélgate de una barra con los brazos extendidos y agarre medio o ancho, las piernas rectas y la pelvis un poco hacia atrás: es la posición inicial.',
      'Sube las piernas hasta que formen 90° con el torso mientras espiras, y aguanta la contracción un segundo.',
      'Baja despacio hasta la posición inicial mientras inspiras.',
    ],
  },
  'Flat_Bench_Lying_Leg_Raise': {
    level: 'beginner',
    primaryMuscles: ['abdominals'],
    secondaryMuscles: [],
    steps: [
      'Túmbate boca arriba en un banco con las piernas extendidas por fuera del extremo.',
      'Pon las manos bajo los glúteos, con las palmas hacia abajo, o agárrate a los lados del banco: es la posición inicial.',
      'Con las piernas lo más rectas posible y las rodillas apenas flexionadas, súbelas hasta formar 90° con el suelo mientras espiras. Aguanta un segundo arriba.',
      'Baja las piernas despacio hasta la posición inicial mientras inspiras.',
    ],
  },
  'Mountain_Climbers': {
    level: 'beginner',
    primaryMuscles: ['quadriceps'],
    secondaryMuscles: ['chest', 'hamstrings', 'shoulders'],
    steps: [
      'Ponte en posición de flexión, con el peso sobre las manos y la punta de los pies.',
      'Flexiona rodilla y cadera para llevar una pierna adelante, con la rodilla más o menos bajo la cadera: es la posición inicial.',
      'Cambia las piernas de forma explosiva: estira la pierna flexionada hasta apoyarla sobre la punta del pie y lleva la otra rodilla adelante.',
      'Sigue alternando durante 20 o 30 segundos.',
    ],
  },
  'Pallof_Press': {
    level: 'beginner',
    primaryMuscles: ['abdominals'],
    secondaryMuscles: ['chest', 'shoulders', 'triceps'],
    steps: [
      'Pon un asidero sencillo en la polea y, si puedes, a la altura del hombro; si no, vale una polea baja.',
      'De lado a la polea, agarra el asidero con las dos manos y aléjate más o menos un brazo de distancia, con el cable en tensión.',
      'Pies a la anchura de la cadera, rodillas algo flexionadas y el asidero en el centro del pecho: es la posición inicial.',
      'Empuja el asidero al frente hasta extender los brazos del todo, con el core firme y activado.',
      'Aguanta unos segundos y vuelve a la posición inicial.',
      'Al acabar la serie, repite mirando hacia el otro lado.',
    ],
  },
  'Plank': {
    level: 'beginner',
    primaryMuscles: ['abdominals'],
    secondaryMuscles: [],
    steps: [
      'Túmbate boca abajo y apóyate en la punta de los pies y los antebrazos, con los codos justo debajo de los hombros.',
      'Mantén el cuerpo recto en todo momento y aguanta la posición todo el tiempo que puedas.',
      'Para hacerlo más difícil, levanta un brazo o una pierna.',
    ],
  },
  'Russian_Twist': {
    level: 'intermediate',
    primaryMuscles: ['abdominals'],
    secondaryMuscles: ['lower back'],
    steps: [
      'Túmbate en el suelo con las rodillas flexionadas y los pies sujetos bajo algo fijo o por un compañero.',
      'Eleva el torso hasta formar una V con los muslos, con los brazos extendidos al frente y las manos juntas: es la posición inicial.',
      'Gira el torso hacia la derecha hasta que los brazos queden paralelos al suelo, mientras espiras.',
      'Aguanta la contracción un segundo, vuelve al centro y repite hacia el lado izquierdo.',
    ],
  },
  'Standing_Cable_Wood_Chop': {
    level: 'beginner',
    primaryMuscles: ['abdominals'],
    secondaryMuscles: ['shoulders'],
    steps: [
      'Pon un asidero sencillo en la polea y súbela a la posición más alta.',
      'De lado a la polea, agarra el asidero con una mano y aléjate más o menos un brazo de distancia, con el cable en tensión y el brazo alineado con él.',
      'Con los pies a la anchura de los hombros, sube la otra mano y agarra el asidero con las dos, manteniendo los brazos extendidos.',
      'En un solo movimiento, tira del asidero hacia abajo y en diagonal hasta la rodilla delantera mientras giras el torso.',
      'Mantén la espalda y los brazos rectos y el core firme; pivota el pie de atrás y flexiona las rodillas para completar el recorrido.',
      'Vuelve despacio y controlado a la posición inicial. Al acabar la serie, repite hacia el otro lado.',
    ],
  },
};
