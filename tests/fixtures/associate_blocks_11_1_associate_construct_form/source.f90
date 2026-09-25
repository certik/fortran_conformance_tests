! rule: R1102
! covers: associate-construct-form
program ab_r1102_form
  implicit none
  integer :: v
  v=1
  associate (a => v)
    a=81
  end associate
  if (v /= 81) then
    write(*,'(a)') 'R1102'
    error stop
  end if
  write(*,'(a)') 'ASSOCIATE BLOCKS R1102 FORM OK'

end program ab_r1102_form
