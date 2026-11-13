import type { ExerciseGuide } from './types';

// No usable Free Exercise DB entry: steps researched from coaching references
// (ACE Fitness, Catalyst Athletics, BarBend and others) and written by us,
// keyed by our own guide id.
export const OWN_GUIDES: Record<string, ExerciseGuide> = {
  'dragon-flag': {
    level: 'expert',
    primaryMuscles: ['abdominals'],
    secondaryMuscles: ['lower back', 'glutes', 'lats'],
    steps: [
      'Túmbate boca arriba en un banco y agarra con fuerza el borde del banco por detrás de la cabeza.',
      'Aprieta abdomen y glúteos y sube las piernas, juntas y estiradas, hasta quedar casi vertical apoyado en la parte alta de la espalda, nunca en el cuello.',
      'Mantén el cuerpo en línea recta de hombros a pies: no dobles las caderas ni las rodillas ni arquees la zona lumbar.',
      'Baja despacio y controlado hasta que el glúteo casi toque el banco, sin que las piernas lleguen a apoyarse.',
      'Vuelve arriba manteniendo la línea recta; si no puedes, flexiona las rodillas o baja solo hasta la mitad.',
    ],
  },
  'toe-to-bar': {
    level: 'intermediate',
    primaryMuscles: ['abdominals'],
    secondaryMuscles: ['lats', 'forearms', 'quadriceps'],
    steps: [
      'Cuélgate de la barra con agarre prono, manos algo más abiertas que los hombros y brazos estirados.',
      'Activa el cuerpo: mete el ombligo, aprieta glúteos y piernas, apunta con los pies y baja los hombros alejándolos de las orejas.',
      'Empuja la barra hacia abajo con las manos, como en un jalón con brazos rectos, para que la cabeza quede detrás de los brazos.',
      'Sube las piernas juntas y lo más rectas que puedas hasta tocar la barra con los dos pies a la vez, entre las manos.',
      'Baja despacio hasta volver a colgar sin balancearte; si aún no llegas, empieza con elevaciones de rodillas.',
    ],
  },
  'landmine-press': {
    level: 'intermediate',
    primaryMuscles: ['shoulders'],
    secondaryMuscles: ['chest', 'triceps', 'abdominals'],
    steps: [
      'Mete un extremo de la barra en el landmine o en una esquina y carga el peso en el otro extremo.',
      'De frente al extremo libre, adelanta un poco el pie contrario al brazo que empuja y sujeta la barra a la altura del hombro con el codo pegado al cuerpo.',
      'Aprieta el abdomen y mantén el torso firme, con una ligera inclinación hacia delante que siga la diagonal de la barra.',
      'Espira y empuja la barra arriba y adelante siguiendo su arco hasta estirar el brazo, sin echarte atrás ni girar el tronco.',
      'Baja controlado hasta el hombro y, al acabar la serie, repite con el otro brazo.',
    ],
  },
  'lateral-raise-machine': {
    level: 'beginner',
    primaryMuscles: ['shoulders'],
    secondaryMuscles: ['traps'],
    steps: [
      'Elige el peso y ajusta el asiento para que el eje de giro quede a la altura de los hombros y las almohadillas justo por encima de los codos.',
      'Siéntate con la espalda pegada al respaldo y los pies en el suelo, apoya la parte exterior de los brazos en las almohadillas y agarra las asas sin apretar.',
      'Aprieta el abdomen y baja los hombros, alejándolos de las orejas; durante toda la serie solo se mueven los brazos.',
      'Empuja las almohadillas con los codos hacia fuera y arriba hasta que los brazos queden paralelos al suelo, sin encoger los hombros.',
      'Aguanta un instante arriba y baja despacio, unos dos segundos, sin dejar que el peso descanse entre repeticiones.',
    ],
  },
  'glute-kickback-machine': {
    level: 'beginner',
    primaryMuscles: ['glutes'],
    secondaryMuscles: ['hamstrings'],
    steps: [
      'Elige el peso, apoya el pecho o las manos en los soportes y planta firme el pie de apoyo, con la cadera libre para moverse sin girar la pelvis.',
      'Coloca el pie de la pierna que trabaja contra la plataforma o el rodillo y mantén la columna neutra y los hombros relajados.',
      'Espira y empuja hacia atrás con el talón extendiendo la cadera, con la rodilla algo flexionada, hasta notar el glúteo bien contraído.',
      'No arquees la zona lumbar ni gires la cadera para llegar más lejos: el movimiento sale solo de la cadera.',
      'Vuelve despacio a la posición inicial sin dejar caer el peso y, al acabar la serie, cambia de pierna.',
    ],
  },
  'push-press': {
    level: 'intermediate',
    primaryMuscles: ['shoulders'],
    secondaryMuscles: ['triceps', 'quadriceps', 'glutes', 'abdominals'],
    steps: [
      'Saca la barra del rack apoyada en la parte delantera de los hombros, con agarre algo más abierto que los hombros y los codos por delante de la barra.',
      'Ponte con los pies a la anchura de las caderas, puntas un poco hacia fuera, y aprieta el abdomen con el torso erguido.',
      'Flexiona las rodillas de forma corta y rápida, como un cuarto de sentadilla, con el tronco vertical y el peso en el medio del pie.',
      'Extiende piernas y caderas con fuerza y, con ese impulso, empuja la barra recta por encima de la cabeza hasta bloquear los codos.',
      'Baja la barra despacio hasta los hombros, estabiliza y repite; no vuelvas a flexionar las rodillas después del impulso.',
    ],
  },
  'side-plank': {
    level: 'intermediate',
    primaryMuscles: ['abdominals'],
    secondaryMuscles: ['glutes', 'abductors', 'shoulders'],
    steps: [
      'Túmbate de lado con las piernas estiradas y los pies uno encima del otro, y apoya el antebrazo con el codo justo debajo del hombro.',
      'Mantén la cabeza alineada con la columna y mira al frente.',
      'Espira, aprieta abdomen y glúteos y levanta la cadera hasta formar una línea recta de la cabeza a los talones, sin girar la cadera.',
      'Aguanta la posición respirando con normalidad, sin que la cadera se hunda.',
      'Baja despacio, cambia de lado y repite; si te cuesta, apoya la rodilla de abajo en lugar del pie.',
    ],
  },
  'cable-lateral-raise': {
    level: 'beginner',
    primaryMuscles: ['shoulders'],
    secondaryMuscles: ['traps'],
    steps: [
      'Pon la polea en la posición más baja con un asa individual y elige un peso ligero.',
      'Ponte de lado a la máquina y coge el asa con la mano más alejada de la polea; apoya la otra mano en la cadera o en el soporte.',
      'Con el codo algo flexionado, espira y sube el brazo hacia fuera, alejándolo de la polea, hasta que el codo llegue a la altura del hombro.',
      'Aguanta un instante arriba sin encoger el hombro ni balancear el tronco.',
      'Inspira y baja despacio hasta la posición inicial; al acabar la serie, cambia de brazo.',
    ],
  },
};
