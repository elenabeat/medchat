REM  *****  BASIC  *****
Sub RemoveImagesFromDraw
    Dim oDoc As Object
    oDoc = ThisComponent

    Dim oPages As Object
    oPages = oDoc.getDrawPages()

    Dim i As Integer
    For i = 0 To oPages.getCount() - 1
        Dim oPage As Object
        oPage = oPages.getByIndex(i)
        
        Dim j As Integer
        j = 0
        Do While j < oPage.getCount()
            Dim oShape As Object
            oShape = oPage.getByIndex(j)
            
            If oShape.supportsService("com.sun.star.drawing.GraphicObjectShape") Then
                oPage.remove(oShape)
            Else
                j = j + 1
            End If
        Loop
    Next i
    
    'Save and close
    oDoc.store()
    oDoc.close(True)
End Sub

Sub ResizeSmallTextAndDeleteHugeText
    Dim oDoc As Object
    oDoc = ThisComponent
    Dim oPages As Object
    oPages = oDoc.getDrawPages()

    Dim i As Integer
    For i = 0 To oPages.getCount() - 1
        Dim oPage As Object
        oPage = oPages.getByIndex(i)

        Dim j As Integer
        j = 0
        Do While j < oPage.getCount()
            Dim oShape As Object
            oShape = oPage.getByIndex(j)

            If oShape.supportsService("com.sun.star.drawing.TextShape") Then
                Dim oText As Object
                oText = oShape.getText()

                If oText.getString() <> "" Then
                    Dim oCursor As Object
                    oCursor = oText.createTextCursor()

                    Dim fontSize As Double
                    fontSize = oCursor.CharHeight

                    If fontSize > 100 Then
                        oPage.remove(oShape)
                        ' Don't increment j since we removed the shape
                    ElseIf fontSize <= 15 Then
                        oCursor.gotoStart(False)
                        oCursor.gotoEnd(True)
                        oCursor.CharHeight = 6
                        j = j + 1
                    Else
                        j = j + 1
                    End If
                Else
                    j = j + 1
                End If
            Else
                j = j + 1
            End If
        Loop
    Next i

    'Save and close
    oDoc.store()
    oDoc.close(True)
End Sub
