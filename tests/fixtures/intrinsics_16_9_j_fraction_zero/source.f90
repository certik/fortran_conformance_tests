program intrinsics_16_9_j_fraction_zero
  implicit none
  integer :: checks
  real :: zero, observed, nonzero_expected
  checks=0
  zero = 0.0
  nonzero_expected = 1.0 / real(radix(1.0), kind=kind(1.0))
  observed = fraction(zero)
  if (observed /= 0.0) then
    write(*,'(a)') 'I16J:fraction_zero:zero-result'
    error stop
  end if
  checks=checks+1
  if (fraction(1.0) /= nonzero_expected) then
    write(*,'(a)') 'I16J:fraction_zero:nonzero-companion'
    error stop
  end if
  checks=checks+1
  select case (checks)
  case (2)
  case default
    write(*,'(a)') 'I16J:check-total'
    error stop
  end select
  write(*,'(a)') 'INTRINSICS 16.9.J FRACTION ZERO OK'
end program intrinsics_16_9_j_fraction_zero
