! rule: S8.4-001
! covers: scalar-integer-and-logical
! Distinctive nonzero/nonblank initialization sentinels are observed before executable overwrite.
program initialization_scalar_integer_logical_effect
  implicit none
  integer :: i = -31417
  logical :: flag = .true.
  integer :: checks
  checks=0
  if (i /= -31417) then
    write(*,'(a)') 'INIT:scalar_integer_logical:integer-initial-value'
    error stop
  end if
  checks=checks+1
  if (.not. flag) then
    write(*,'(a)') 'INIT:scalar_integer_logical:logical-true-initial-value'
    error stop
  end if
  checks=checks+1
  if (checks /= 2) then
    write(*,'(a)') 'INIT:scalar_integer_logical:check-total'
    error stop
  end if
  write(*,'(a)') 'INITIALIZATION SCALAR INTEGER LOGICAL OK'
end program initialization_scalar_integer_logical_effect
