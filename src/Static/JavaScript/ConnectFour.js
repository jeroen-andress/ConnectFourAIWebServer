var White = 2;
var Red = 1;
var None = 0;
var Winner = None;
var IsTied = false;
var MoveInProcess = false;

jQuery(document).ready(DocumentLoaded); 

function DocumentLoaded()
{
    var request = jQuery.ajax({type: "GET", url: "GetPlayboard", type: "POST", data: {"session": GetSession()}});
    request.done(InitPlayboard);
    request.fail(AjaxError);

    UpdateStatistics();
}

function GetSession()
{
    return jQuery("body").attr("session");
}

function AjaxError(jqXHR, textStatus) 
{
    alert("Ajax request failed: " + textStatus);
}

function UpdateStatistics()
{
     jQuery.ajax({type: "GET", url: "GetStatistics", type: "POST", data: {"session": GetSession()}}).done(function(data)
     {
          statistics = jQuery.parseJSON(data);
          
          var statisticNode = jQuery("#statistic");

          statisticNode.text('You win ' + statistics["WhiteWins"] + ' time(s), you lose ' + statistics["RedWins"] + ' time(s), tied ' + statistics["Tied"] + ' time(s)');
     });

}

function InitPlayboard(data)
{
    playboard = jQuery.parseJSON(data);
    rows = playboard.length;
    columns = playboard.length;
        
    var playboardNode = jQuery("#playboard");
        
    jQuery.each(playboard, function(i, column)
    {
        playboardNode.append('<div id=\'row' + i + '\'>');
        jQuery.each(column, function(j, field)
        {
            jQuery('#row' + i).append('<img class="field" id="field' + i + '' + j + '" />');
            SetField(i, j, field);
            
            jQuery('#field' + i + '' + j).hover(function() 
            {
                if (Winner != None || IsTied)
                {
                    return;
                }
                
                jQuery(this).css('cursor', 'pointer');
                ColumnMouseOverEnter(playboard, j);
            }, function() 
            {
                if (Winner != None || IsTied)
                {
                    return;
                }
                
                jQuery(this).css('cursor', 'auto');
                ColumnMouseOverLeave(playboard, j);
            });

            jQuery('#field' + i + '' + j).click(function()
            {
                if (Winner != None || IsTied)
                {
                    return;
                }
                
                ChooseColumn(playboard, j);
            });
           
        });
    });
}

function GetFreeFieldInColumn(playboard, column)
{
    if (playboard[0][column] != None)
    {
        return -1;
    }
    
    i = 0;
    for (; i < playboard.length && playboard[i][column] == 0; i++);
    return i - 1;
}

function ColumnMouseOverEnter(playboard, column)
{
    if (! MoveInProcess)
    {
         var row = GetFreeFieldInColumn(playboard, column);
         
         if (row >= 0)
         {
             SetField(row, column, White);
         }
    }
}

function SetField(row, column, player)
{
    playerImages = {0: 'static/Images/None.png', 1: 'static/Images/Red.png', 2: 'static/Images/White.png'};
    jQuery('#field' + row + '' + column).attr('src', playerImages[player]);
}

function ColumnMouseOverLeave(playboard, column)
{
    var row = GetFreeFieldInColumn(playboard, column);
    
    if (row >= 0)
    {
        SetField(row, column, None);
    }
}

function ChooseColumn(playboard, column)
{
    if (! MoveInProcess)
    {
         var row = GetFreeFieldInColumn(playboard, column);
         
         if (row < 0)
         {
             alert("Column is full. Choose an other.");
             return;
         }
    
         MoveInProcess = true;
         jQuery.ajax({type: "GET", url: "ChooseColumn/" + column, type: "POST", data: {"session": GetSession()}}).done(function(data)
         {
             aimColumn = parseInt(data);

	        if (aimColumn >= 0 && aimColumn <= 6)
	        {
                    ColumnInsertEffect(playboard, Red, aimColumn, function()
                    {
                        aimRow = GetFreeFieldInColumn(playboard, aimColumn);
                        SetField(aimRow, aimColumn, Red);
                        playboard[aimRow][aimColumn] = White;
    
                        MoveInProcess = false;
                        
                        EndOfGame();
                    });
	        }
         });    
         
         SetField(row, column, None);
         ColumnInsertEffect(playboard, White, column, function()
         {
             SetField(row, column, White);
             playboard[row][column] = White;

	     EndOfGame();
         });
    }
}

function ColumnInsertEffect(playboard, player, column, callback, row)
{
    if (row == null)
    {
        row = 0;
    }
    
    if (row >= GetFreeFieldInColumn(playboard, column))
    {
        if (callback != null)
        {
            callback();
        }
        
        return;
    }
    
    SetField(row, column, player);
    var node = jQuery('#field' + row + '' + column);
//     node.fadeIn(250);
    node.fadeOut(250, function()
    {
        SetField(row, column, None);
        node.show();
        ColumnInsertEffect(playboard, player, column, callback, row + 1);
    });
}

function EndOfGame()
{
    jQuery.ajax({type: "GET", url: "GetWinner", type: "POST", data: {"session": GetSession()}}).done(function(data)
    {
        Winner = parseInt(data);
        if (Winner != None)
        {
            if (Winner == White)
            {
                alert("Congratulations! You have won.");
            }
            else
            {
                alert("You lost");
            }

            Reset();
        }
    });
        
    jQuery.ajax({type: "GET", url: "IsTied", type: "POST", data: {"session": GetSession()}}).done(function(data)
    {
        if (data == "true")
        {
            IsTied = true;
            alert("End of game. Tied");

            Reset();
        }
        else
        {
            IsTied = false;
        }
    });
    
//     jQuery.ajax({type: "GET", url: "GetPlayboard"}).done(InitPlayboard);
}

function Reset()
{
    jQuery.ajax({type: "GET", url: "Reset", type: "POST", data: {"session": GetSession()}}).done(function(data)
    {
         Winner = None;
         IsTied = false;
         MoveInProcess = false;

         DocumentLoaded()
    });
}
