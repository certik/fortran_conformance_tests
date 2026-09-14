      program p                                                         
      implicit none                                                     
      character(len=59) :: text                                         
      text=repeat('?',59)                                               
      text='AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAZ'
      if (text(1:58)/=repeat('A',58)) error stop 1                      
      if (text(59:59)/='Z') error stop 2                                
      end program p                                                     
