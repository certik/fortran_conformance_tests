! rule: R1125
! covers: concurrent-header-with-integer-type-spec
program do_construct_form_concurrent_header_with_type
  implicit none
  integer :: trace(4)
  trace = -777
  do concurrent (integer :: i = 1:4)
    trace(i) = 10 + i
  end do
  if (any(trace /= [11, 12, 13, 14])) then
    write(*,'(a)') 'DCF:do_construct_form_concurrent_header_with_type:trace'
    error stop
  end if
  if (count(trace /= -777) /= 4) then
    write(*,'(a)') 'DCF:do_construct_form_concurrent_header_with_type:count'
    error stop
  end if
  write(*,'(a)') 'DO CONSTRUCT FORM DO CONSTRUCT FORM CONCURRENT HEADER WITH TYPE OK'
end program do_construct_form_concurrent_header_with_type
