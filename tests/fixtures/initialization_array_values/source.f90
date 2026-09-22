! rule: S8.4-001
! covers: array-values
! Distinctive nonzero/nonblank initialization sentinels are observed before executable overwrite.
program initialization_array_values_effect
  implicit none
  integer :: v(4:6) = [2,3,5]
  integer :: checks
  checks=0
  if (lbound(v,1) /= 4) then
    write(*,'(a)') 'INIT:array_values:v-lbound'
    error stop
  end if
  checks=checks+1
  if (ubound(v,1) /= 6) then
    write(*,'(a)') 'INIT:array_values:v-ubound'
    error stop
  end if
  checks=checks+1
  if (v(4) /= 2) then
    write(*,'(a)') 'INIT:array_values:v4'
    error stop
  end if
  checks=checks+1
  if (v(5) /= 3) then
    write(*,'(a)') 'INIT:array_values:v5'
    error stop
  end if
  checks=checks+1
  if (v(6) /= 5) then
    write(*,'(a)') 'INIT:array_values:v6'
    error stop
  end if
  checks=checks+1
  if (checks /= 5) then
    write(*,'(a)') 'INIT:array_values:check-total'
    error stop
  end if
  write(*,'(a)') 'INITIALIZATION ARRAY VALUES OK'
end program initialization_array_values_effect
