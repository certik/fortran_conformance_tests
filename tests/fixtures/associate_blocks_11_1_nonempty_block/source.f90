! rule: R1101
! covers: nonempty-block-form
program ab1101_nonempty
  implicit none
  integer :: marker
  marker=-7
  block
    marker=41
  end block
  if (marker /= 41) then
    write(*,'(a)') 'R1101-NONEMPTY'
    error stop
  end if
  write(*,'(a)') 'ASSOCIATE BLOCKS NONEMPTY BLOCK OK'

end program ab1101_nonempty
