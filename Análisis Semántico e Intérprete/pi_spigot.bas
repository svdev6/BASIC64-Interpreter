10 PRINT "ENTER THE NUMBER OF PI DIGITS YOU WISH TO PRINT, FOR A MAXIMUM OF 10: ";
20 INPUT N
30  LET L = INT((10 * N) / 3)
40  DIM a(33)
50  FOR J = 1 TO L
60     LET a(J) = 2
70  NEXT J
80  LET T = 0
90  LET P = 0
100 FOR J = 1 TO N
110   LET   q = 0
120   FOR I = L TO 1 STEP -1
130     LET x = (10 * a(I)) + (q * I)
140     LET a(I) = INT(x - INT(x / (2 * I - 1)) * (2 * I - 1)) 
150     LET q = INT(x / (2 * I - 1))
160   NEXT I
170   LET a(1) = q - INT(q / 10) * 10
180   LET q = INT(q / 10)
190   IF q = 9 THEN 200
200     LET T = T + 1
205     GOTO 290
210   IF q = 10 THEN 220
220     PRINT P + 1
230     FOR k = 1 TO T
240       PRINT
250     NEXT k
260     LET P = 0
270     LET T = 0
280     GOTO 380
290   IF P <= 0 THEN 300
295     PRINT P;
300   LET P = q
310   IF T <> 0 THEN 350
350     LET T = 0
380 NEXT J
390 END
