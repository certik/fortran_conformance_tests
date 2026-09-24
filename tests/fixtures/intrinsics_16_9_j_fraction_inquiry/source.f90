program intrinsics_16_9_j_fraction_inquiry
  implicit none
  integer :: checks
  real :: expected, observed
  checks=0
  expected = 1.0 / real(radix(1.0), kind=kind(1.0))
  observed = fraction(1.0)
  if (observed /= expected) then
    write(*,'(a)') 'I16J:fraction_inquiry:model-fraction'
    error stop
  end if
  checks=checks+1
  select case (checks)
  case (1)
  case default
    write(*,'(a)') 'I16J:check-total'
    error stop
  end select
  write(*,'(a)') 'INTRINSICS 16.9.J FRACTION INQUIRY OK'
end program intrinsics_16_9_j_fraction_inquiry
