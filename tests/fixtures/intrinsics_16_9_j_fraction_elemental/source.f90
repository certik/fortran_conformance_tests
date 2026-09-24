program intrinsics_16_9_j_fraction_elemental
  implicit none
  integer :: checks
  real :: values(3), observed(3), expected(3)
  checks=0
  values = [0.0, 1.0, real(radix(1.0), kind=kind(1.0))]
  expected = [0.0, 1.0 / real(radix(1.0), kind=kind(1.0)), 1.0 / real(radix(1.0), kind=kind(1.0))]
  observed = fraction(values)
  if (any(observed /= expected)) then
    write(*,'(a)') 'I16J:fraction_elemental:elementwise-values'
    error stop
  end if
  checks=checks+1
  if (any(shape(fraction(values)) /= [3])) then
    write(*,'(a)') 'I16J:fraction_elemental:elementwise-shape'
    error stop
  end if
  checks=checks+1
  select case (checks)
  case (2)
  case default
    write(*,'(a)') 'I16J:check-total'
    error stop
  end select
  write(*,'(a)') 'INTRINSICS 16.9.J FRACTION ELEMENTAL OK'
end program intrinsics_16_9_j_fraction_elemental
