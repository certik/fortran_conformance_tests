! rule: S11.1.3.2-003
! covers: declared-type-control
program ab1132_declared_type
  implicit none
  type :: packet
    integer :: tag
  end type packet
  type(packet) :: item
  integer :: result
  item%tag=91; result=-1
  associate (alias => item)
    result=alias%tag
  end associate
  if (result /= 91) then
    write(*,'(a)') 'DECLTYPE'
    error stop
  end if
  write(*,'(a)') 'ASSOCIATE BLOCKS DECLARED TYPE OK'

end program ab1132_declared_type
