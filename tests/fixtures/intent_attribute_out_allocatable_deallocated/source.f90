program p
implicit none
integer, allocatable :: actual(:)
allocate(actual(5))
actual = [1,2,3,4,5]
call observe_out_allocatable(actual)
if (.not. allocated(actual)) error stop 1
if (size(actual) /= 2) error stop 2
if (any(actual /= [31,37])) error stop 3
write(*,'(a)') 'INTENT ATTRIBUTE OUT ALLOCATABLE DEALLOCATED OK'
contains
subroutine observe_out_allocatable(x)
  integer, allocatable, intent(out) :: x(:)
  if (allocated(x)) error stop 4
  allocate(x(2))
  x = [31,37]
end subroutine
end program p
