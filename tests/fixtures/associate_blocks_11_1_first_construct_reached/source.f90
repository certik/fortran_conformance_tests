! rule: S11.1.2.2-001
! covers: first-construct-reached
program ab1122_first
  implicit none
  integer :: first_value, second_value
  first_value=-8; second_value=-9
  block
    first_value=101
    second_value=first_value+1
  end block
  if (first_value /= 101) then
    write(*,'(a)') 'FIRST'
    error stop
  end if
  if (second_value /= 102) then
    write(*,'(a)') 'SECOND'
    error stop
  end if
  write(*,'(a)') 'ASSOCIATE BLOCKS FIRST CONSTRUCT OK'

end program ab1122_first
