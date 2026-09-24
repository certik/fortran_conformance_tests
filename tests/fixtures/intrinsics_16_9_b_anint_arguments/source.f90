program intrinsics_16_9_b_anint_arguments
  implicit none
  integer :: checks
  real(kind=kind(0.0d0)) :: high
  real :: observed
  checks=0
  high = 2.25d0
  observed = anint(2.25)
  if (observed /= 2.0) then
    write(*,'(a)') 'I16B:anint_arguments:real-argument'
    error stop
  end if
  checks=checks+1
  observed = anint(high, kind=kind(0.0))
  if (kind(anint(high, kind=kind(0.0))) /= kind(0.0)) then
    write(*,'(a)') 'I16B:anint_arguments:constant-kind'
    error stop
  end if
  checks=checks+1
  select case (checks)
  case (2)
  case default
    write(*,'(a)') 'I16B:anint_arguments:check-total'
    error stop
  end select
  write(*,'(a)') 'INTRINSICS 16.9.B ANINT ARGUMENTS OK'
end program intrinsics_16_9_b_anint_arguments
