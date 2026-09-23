program allocate_statement_c944_scalar_no_shape
  implicit none
  integer, allocatable :: x
  integer :: checks
  checks=0
  allocate(x)
  if (.not. allocated(x)) then
    write(*,'(a)') 'ASTMT:c944_scalar_no_shape:scalar-allocated'
    error stop
  end if
  checks=checks+1
  x=41
  if (x /= 41) then
    write(*,'(a)') 'ASTMT:c944_scalar_no_shape:scalar-payload'
    error stop
  end if
  checks=checks+1
  if (checks /= 2) then
    write(*,'(a)') 'ASTMT:c944_scalar_no_shape:check-total'
    error stop
  end if
  checks=checks+1
  write(*,'(a)') 'ALLOCATE STATEMENT C944 SCALAR NO SHAPE OK'
end program allocate_statement_c944_scalar_no_shape
