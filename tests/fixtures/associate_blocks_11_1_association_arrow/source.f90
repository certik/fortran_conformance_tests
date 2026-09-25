! rule: R1104
! covers: association-arrow-form, associate-name-binding-source
program ab_r1104_assoc
  implicit none
  integer :: selector, result
  selector=14; result=-1
  associate (alias => selector)
    alias=28
    result=alias
  end associate
  if (selector /= 28) then
    write(*,'(a)') 'ARROW'
    error stop
  end if
  if (result /= 28) then
    write(*,'(a)') 'BIND'
    error stop
  end if
  write(*,'(a)') 'ASSOCIATE BLOCKS R1104 ASSOC OK'

end program ab_r1104_assoc
