! rule: C1101
! covers: definable-variable-selector-control
program ab_c1101_control
  implicit none
  integer :: store(4), idx(2)
  store=[1,2,3,4]; idx=[1,3]
  associate (section => store(2:4))
    section=[20,30,40]
  end associate
  if (store(2) /= 20) then
    write(*,'(a)') 'C1101A'
    error stop
  end if
  if (store(4) /= 40) then
    write(*,'(a)') 'C1101B'
    error stop
  end if
  write(*,'(a)') 'ASSOCIATE BLOCKS C1101 CONTROL OK'

end program ab_c1101_control
