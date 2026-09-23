! rule: S9.7.3.2-001
! covers: unallocated-allocatable-deallocate-error
! The object is first proved allocated with nonunit bounds and nonzero values, then deallocated.
program dealloc_unallocated_error
  use iso_fortran_env, only: stat_stopped_image, stat_failed_image
  implicit none
  integer, allocatable :: x(:)
  integer :: stat, checks
  checks = 0

  allocate(x(-3:-1), stat=stat)
  if (stat /= 0) error stop 'D9732:unallocated:initial-allocate-stat'
  x = [37, 41, 43]
  if (.not. allocated(x)) error stop 'D9732:unallocated:initial-allocated'
  checks = checks + 1
  if (lbound(x,1) /= -3) error stop 'D9732:unallocated:initial-lower'
  checks = checks + 1
  if (ubound(x,1) /= -1) error stop 'D9732:unallocated:initial-upper'
  checks = checks + 1
  if (any(x /= [37, 41, 43])) error stop 'D9732:unallocated:initial-values'
  checks = checks + 1

  deallocate(x, stat=stat)
  if (stat /= 0) error stop 'D9732:unallocated:first-deallocate-stat'
  checks = checks + 1
  if (allocated(x)) error stop 'D9732:unallocated:first-deallocated'
  checks = checks + 1

  stat = -777
  deallocate(x, stat=stat)
  if (stat <= 0) error stop 'D9732:unallocated:error-stat-positive'
  checks = checks + 1
  if (stat == stat_stopped_image .or. stat == stat_failed_image) error stop 'D9732:unallocated:error-stat-not-image'
  checks = checks + 1
  if (allocated(x)) error stop 'D9732:unallocated:remains-unallocated'
  checks = checks + 1

  allocate(x(5:7), stat=stat)
  if (stat /= 0) error stop 'D9732:unallocated:reallocate-stat'
  x = [53, 59, 61]
  if (lbound(x,1) /= 5) error stop 'D9732:unallocated:realloc-lower'
  checks = checks + 1
  if (ubound(x,1) /= 7) error stop 'D9732:unallocated:realloc-upper'
  checks = checks + 1
  if (any(x /= [53, 59, 61])) error stop 'D9732:unallocated:realloc-values'
  checks = checks + 1
  if (checks /= 12) error stop 'D9732:unallocated:check-total'
  write(*,'(a)') 'DEALLOC UNALLOCATED ERROR OK'
end program dealloc_unallocated_error
