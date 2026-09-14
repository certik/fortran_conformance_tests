      program p                                                         
      implicit none                                                     
      character(len=2) :: record                                        
      integer :: ios                                                    
      record='??'                                                       
      ios=99                                                            
      write(record,10,iostat=ios) 7                                     
      if (ios/=0) error stop 1                                          
      if (record/=' 7') error stop 2                                    
   10 format ( I   2 )                                                  
      end program p                                                     
