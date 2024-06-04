# basircode.py
'''
Una Máquina "Virtual" Intermedia
================================
Una CPU real normalmente consta de registros y un pequeño conjunto básico de 
opcodes  para realizar cálculos matemáticos, cargar/almacenar valores desde 
la memoria y flujo de control básico (ramificaciones, saltos, etc.).
Aunque puedes hacer que un compilador genere instrucciones directamente para 
una CPU, a menudo es más sencillo apuntar a un nivel más alto de abstracción. 
Una de esas abstracciones es la de una máquina de pila.

Por ejemplo, supongamos que desea evaluar una operación como esta:

    LET A = 2 + 3 * 4 - 5

Para evaluar la expresión anterior, podría generar pseudo-instrucciones 
como esta:

    CONSTI 2      ; stack = [2]
    CONSTI 3      ; stack = [2, 3]
    CONSTI 4      ; stack = [2, 3, 4]
    MULI          ; stack = [2, 12]
    ADDI          ; stack = [14]
    CONSTI 5      ; stack = [14, 5]
    SUBI          ; stack = [9]
    LOCAL_SET "A" ; stack = []

Observe que aquí no hay detalles sobre los registros de la CPU ni nada por 
el estilo.  Es mucho más simple (un módulo de nivel inferior puede determinar 
el mapeo del hardware más adelante si es necesario).

Las CPU suelen tener un pequeño conjunto de tipos de datos de código, como 
números enteros y flotantes. Hay instrucciones dedicadas para cada tipo. 
El código IR seguirá el mismo principio al admitir operaciones con números 
enteros y de punto flotante.  Por ejemplo:

    ADDI   ; Integer add
    ADDF   ; Float add

Aunque el lenguaje de entrada puede tener otros tipos como 'bool' y 'char', 
esos tipos deben asignarse a números enteros o flotantes. Por ejemplo, un 
bool se puede representar mediante un número entero con valores {0, 1}. 
Un carácter se puede representar mediante un número entero cuyo valor es el 
mismo que el valor del código de carácter (es decir, un código ASCII o un 
punto de código Unicode).

Con eso en mente, aquí hay un conjunto de instrucciones básicas para nuestro 
Código IR:

    ; Operaciones Enteras
    CONSTI  value            ; Push a integer literal on the stack
    ADDI                     ; Add top two items on stack
    SUBI                     ; Substract top two items on stack
    MULI                     ; Multiply top two items on stack
    DIVI                     ; Divide top two items on stack
    ANDI                     ; Bitwise AND
    ORI                      ; Bitwise OR
    LTI                      : <
    LEI                      : <=
    GTI                      : >
    GEI                      : >=
    EQI                      : ==
    NEI                      : !=
    PRINTI                   ; Print top item on stack
    PEEKI                    ; Get integer from memory (address on stack)
    POKEI                    ; Put integer in memory (value, address) on stack.
    ITOF                     ; Convert integer to float

    ; Operaciones de punto flotante
    CONSTF value             ; Push a float literal
    ADDF                     ; Add top two items on stack
    SUBF                     ; Substract top two items on stack
    MULF                     ; Multiply top two items on stack
    DIVF                     ; Divide top two items on stack
    LTF                      : <
    LEF                      : <=
    GTF                      : >
    GEF                      : >=
    EQF                      : ==
    NEF                      : !=
    PRINTF                   ; Print top item on stack
    PEEKF                    ; Get float from memory (address on stack)
    POKEF                    ; Put float in memory (value, address on stack) 
    FTOI                     ; Convert float to integer

    ; Byte-oriented operations (values are presented as integers)    
    PRINTB                   ; Print top item on stack
    PEEKB                    ; Get byte from memory (address on stack)
    POKEB                    ; Put byte in memory (value, address on stack)

    ; Variable load/store.
    ; These instructions read/write both local and global variables. Variables
    ; are referenced by some kind of name that identifies the variable.  The management
    ; and declaration of these names must also be handled by your code generator.
    ; However, variable declarations are not a normal "instruction."  Instead, it's
    ; a kind of data that needs to be associated with a module or function.
    LOCAL_GET name           ; Read a local variable onto stack
    LOCAL_SET name           ; Save local variable from stack
    GLOBAL_GET name          ; Read a global variable onto the stack
    GLOBAL_SET name          ; Save a global variable from the stack

    ; Function call and return.
    ; Functions are referenced by name.   Your code generator will need to figure
    ; out some way to manage these names.
    CALL name                ; Call function. All arguments must be on stack
    RET                      ; Return from a function. Value must be on stack

    ; Structured control flow
    IF                       ; Start consequence part of an "if". Test on stack
    ELSE                     ; Start alternative part of an "if".
    ENDIF                    ; End of an "if" statement.

    LOOP                     ; Start of a loop
    CBREAK                   ; Conditional break. Test on stack.
    CONTINUE                 ; Go back to loop start
    ENDLOOP                  ; End of a loop

    ; Memory
    GROW                     ; Increment memory (size on stack) (returns new size)

Una palabra sobre el acceso a la memoria... las instrucciones PEEK y POKE se 
utilizan para acceder a direcciones de memoria sin procesar. Ambas instrucciones 
requieren que una dirección de memoria esté en la pila *primero*. Para la 
instrucción POKE, el valor que se almacena se inserta después de la dirección. 
El orden es importante y es fácil estropearlo. Así que preste mucha atención a eso.


Tu tarea
=========
Su tarea es la siguiente: escribir código que recorra la estructura del 
programa y lo aplane en una secuencia de instrucciones representadas como 
tuplas de la forma:

       (operation, operands, ...)

Por ejemplo, el código en la parte superior podría terminar luciendo así:

    code = [
       ('CONSTI', 2),
       ('CONSTI', 3),
       ('CONSTI', 4),
       ('MULI',),
       ('ADDI',),
       ('CONSTI', 5),
       ('SUBI',),
       ('LOCAL_SET', 'A'),
    ]

Funciones
=========
Todo el código generado está asociado con algún tipo de función. Por ejemplo, 
con una función definida por el usuario como esta:

    func fact(n int) int {
        var result int = 1;
        var x int = 1;
        while x <= n {
            result = result * x;
            x = x + 1;
        }
     }

Debe crear un objeto Función que contenga el nombre de la función, los 
argumentos, el tipo de retorno, las variables locales y un cuerpo que contenga 
todas las instrucciones de bajo nivel. Nota: en este nivel, los tipos 
representarán tipos de IR de bajo nivel como Integer (I) y Float (F). No son 
los mismos tipos que se utilizan en el código  BASIC de alto nivel.

Además, todo el código definido *fuera* de una función aún debe ir a una 
función llamada "_init()". Por ejemplo, si tiene declaraciones globales 
como esta:

     const pi = 3.14159;
     const r = 2.0;
     print pi*r*r;

Su generador de código debería tratarlos así:

     func _init() int {
         const pi = 3.14159;
         const r = 2.0;
         print pi*r*r;
         return 0;
     }

En pocas palabras: todo el código va a una función.

Módulos
=======
El resultado final de la generación de código debe ser algún tipo de objeto 
Módulo que contenga todo. El módulo incluye objetos de función, variables 
globales y cualquier otra cosa que pueda necesitar para generar código más 
adelante.
'''
