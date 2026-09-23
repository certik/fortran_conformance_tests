! rule: R1129
! covers: single-locality-spec
program do_construct_form_single_locality
  implicit none
  integer :: trace(4)
  integer :: i
  integer :: offset
  trace = -777
  offset = 30
  do concurrent (i = 1:4) shared(offset)
    trace(i) = offset + i
  end do
  if (any(trace /= [31, 32, 33, 34])) then
    write(*,'(a)') 'DCF:do_construct_form_single_locality:trace'
    error stop
  end if
  if (count(trace /= -777) /= 4) then
    write(*,'(a)') 'DCF:do_construct_form_single_locality:count'
    error stop
  end if
  write(*,'(a)') 'DO CONSTRUCT FORM DO CONSTRUCT FORM SINGLE LOCALITY OK'
end program do_construct_form_single_locality
