! rule: R1130
! covers: default-none-locality
program do_construct_form_default_none
  implicit none
  integer :: trace(4)
  integer :: i
  integer :: offset
  trace = -777
  offset = 30
  do concurrent (i = 1:4) default(none) shared(trace, offset)
    trace(i) = offset + i
  end do
  if (any(trace /= [31, 32, 33, 34])) then
    write(*,'(a)') 'DCF:do_construct_form_default_none:trace'
    error stop
  end if
  if (count(trace /= -777) /= 4) then
    write(*,'(a)') 'DCF:do_construct_form_default_none:count'
    error stop
  end if
  write(*,'(a)') 'DO CONSTRUCT FORM DO CONSTRUCT FORM DEFAULT NONE OK'
end program do_construct_form_default_none
