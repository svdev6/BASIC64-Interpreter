10 FOR Y = -12 TO 12
20   FOR X = -39 TO 39
30     LET C1 = X * 0.0458
40     LET C2 = Y * 0.08333
50     LET A = C1
60     LET B = C2
70     FOR I = 0 TO 15
80       LET T = A * A - B * B + C1
90       LET B = 2 * A * B + C2
100       LET A = T
110       IF (A * A + B * B) > 4 THEN 200
120     NEXT I
130     PRINT " ";
200     IF I <= 9 THEN 205
202     LET I = I + 7
205     PRINT ".";
210   NEXT X
220   PRINT
230 NEXT Y
240 END 
