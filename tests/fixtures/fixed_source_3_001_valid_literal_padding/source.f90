      program p                                                         
      implicit none                                                     
      character(len=61) :: text                                         
      text=repeat('?',61)                                               
      text='A                                                           
     ;B'                                                                
      if (text(1:1)/='A') error stop 1                                  
      if (text(2:60)/=repeat(' ',59)) error stop 2                      
      if (text(61:61)/='B') error stop 3                                
      end program p                                                     
