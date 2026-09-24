program expr_conditional_characteristics
  use iso_fortran_env, only: int32
  implicit none
  integer :: checks, x
  checks=0
  if (kind((.true. ? 3_int32 : 4_int32)) /= int32) error stop 'EC1004:kind'
  if ((.true. ? 3_int32 : 4_int32) /= 3_int32) error stop 'EC1004:value'
  checks=checks+1
  x = (.false. ? 10_int32 : .true. ? 20_int32 : 30_int32)
  if (x /= 20) error stop 'EC1004:nested'
  checks=checks+1
  if (checks /= 2) error stop 'EC1004:checks'
  write(*,'(a)') 'EXPRESSIONS CONDITIONAL CHARACTERISTICS OK'
end program expr_conditional_characteristics
