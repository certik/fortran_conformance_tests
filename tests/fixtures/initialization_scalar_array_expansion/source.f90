! rule: S8.4-001
! covers: scalar-array-expansion
! Distinctive nonzero/nonblank initialization sentinels are observed before executable overwrite.
program initialization_scalar_array_expansion_effect
  implicit none
  integer :: a(-3:-1) = -24681
  integer :: b(5:6,-2:0) = 13579
  integer :: checks
  checks=0
  if (lbound(a,1) /= -3) then
    write(*,'(a)') 'INIT:scalar_array_expansion:a-lbound'
    error stop
  end if
  checks=checks+1
  if (ubound(a,1) /= -1) then
    write(*,'(a)') 'INIT:scalar_array_expansion:a-ubound'
    error stop
  end if
  checks=checks+1
  if (lbound(b,1) /= 5) then
    write(*,'(a)') 'INIT:scalar_array_expansion:b-lbound-1'
    error stop
  end if
  checks=checks+1
  if (ubound(b,1) /= 6) then
    write(*,'(a)') 'INIT:scalar_array_expansion:b-ubound-1'
    error stop
  end if
  checks=checks+1
  if (lbound(b,2) /= -2) then
    write(*,'(a)') 'INIT:scalar_array_expansion:b-lbound-2'
    error stop
  end if
  checks=checks+1
  if (ubound(b,2) /= 0) then
    write(*,'(a)') 'INIT:scalar_array_expansion:b-ubound-2'
    error stop
  end if
  checks=checks+1
  if (a(-3) /= -24681) then
    write(*,'(a)') 'INIT:scalar_array_expansion:a--3'
    error stop
  end if
  checks=checks+1
  if (a(-2) /= -24681) then
    write(*,'(a)') 'INIT:scalar_array_expansion:a--2'
    error stop
  end if
  checks=checks+1
  if (a(-1) /= -24681) then
    write(*,'(a)') 'INIT:scalar_array_expansion:a--1'
    error stop
  end if
  checks=checks+1
  if (b(5,-2) /= 13579) then
    write(*,'(a)') 'INIT:scalar_array_expansion:b-5--2'
    error stop
  end if
  checks=checks+1
  if (b(5,-1) /= 13579) then
    write(*,'(a)') 'INIT:scalar_array_expansion:b-5--1'
    error stop
  end if
  checks=checks+1
  if (b(5,0) /= 13579) then
    write(*,'(a)') 'INIT:scalar_array_expansion:b-5-0'
    error stop
  end if
  checks=checks+1
  if (b(6,-2) /= 13579) then
    write(*,'(a)') 'INIT:scalar_array_expansion:b-6--2'
    error stop
  end if
  checks=checks+1
  if (b(6,-1) /= 13579) then
    write(*,'(a)') 'INIT:scalar_array_expansion:b-6--1'
    error stop
  end if
  checks=checks+1
  if (b(6,0) /= 13579) then
    write(*,'(a)') 'INIT:scalar_array_expansion:b-6-0'
    error stop
  end if
  checks=checks+1
  if (checks /= 15) then
    write(*,'(a)') 'INIT:scalar_array_expansion:check-total'
    error stop
  end if
  write(*,'(a)') 'INITIALIZATION SCALAR ARRAY EXPANSION OK'
end program initialization_scalar_array_expansion_effect
