! rule: S8.4-001
! covers: integer-kind-conversion
! Distinctive nonzero/nonblank initialization sentinels are observed before executable overwrite.
program initialization_integer_kind_conversion_effect
  implicit none
  integer, parameter :: wide_k = selected_int_kind(18)
  integer(kind=wide_k), parameter :: wide_source = 2719_wide_k
  integer(kind=wide_k) :: wide = -31417
  integer :: narrow = wide_source
  integer :: checks
  checks=0
  if (wide /= -31417) then
    write(*,'(a)') 'INIT:integer_kind_conversion:default-to-selected'
    error stop
  end if
  checks=checks+1
  if (narrow /= 2719) then
    write(*,'(a)') 'INIT:integer_kind_conversion:selected-to-default'
    error stop
  end if
  checks=checks+1
  if (checks /= 2) then
    write(*,'(a)') 'INIT:integer_kind_conversion:check-total'
    error stop
  end if
  write(*,'(a)') 'INITIALIZATION INTEGER KIND CONVERSION OK'
end program initialization_integer_kind_conversion_effect
