program allocate_statement_creation
  implicit none
  integer, allocatable :: x
  integer, pointer :: ptr
  integer :: checks
  checks=0
  allocate(x)
  if (.not. allocated(x)) then
    write(*,'(a)') 'ASTMT:creation:allocatable-created'
    error stop
  end if
  checks=checks+1
  x=17
  if (x /= 17) then
    write(*,'(a)') 'ASTMT:creation:allocatable-payload'
    error stop
  end if
  checks=checks+1
  allocate(ptr)
  if (.not. associated(ptr)) then
    write(*,'(a)') 'ASTMT:creation:pointer-created'
    error stop
  end if
  checks=checks+1
  ptr=23
  if (ptr /= 23) then
    write(*,'(a)') 'ASTMT:creation:pointer-payload'
    error stop
  end if
  checks=checks+1
  if (checks /= 4) then
    write(*,'(a)') 'ASTMT:creation:check-total'
    error stop
  end if
  checks=checks+1
  write(*,'(a)') 'ALLOCATE STATEMENT CREATION OK'
end program allocate_statement_creation
