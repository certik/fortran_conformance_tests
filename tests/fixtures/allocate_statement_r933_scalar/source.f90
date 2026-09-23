program allocate_statement_r933_scalar
  implicit none
  integer, allocatable :: x
  integer :: checks
  checks=0
  allocate(x)
  if (.not. allocated(x)) then
    write(*,'(a)') 'ASTMT:r933_scalar:scalar-allocated'
    error stop
  end if
  checks=checks+1
  x=41
  if (x /= 41) then
    write(*,'(a)') 'ASTMT:r933_scalar:scalar-payload'
    error stop
  end if
  checks=checks+1
  if (checks /= 2) then
    write(*,'(a)') 'ASTMT:r933_scalar:check-total'
    error stop
  end if
  checks=checks+1
  write(*,'(a)') 'ALLOCATE STATEMENT R933 SCALAR OK'
end program allocate_statement_r933_scalar
