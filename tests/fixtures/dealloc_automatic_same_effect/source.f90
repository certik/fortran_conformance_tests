! rule: S9.7.3.2-014
! covers: automatic-deallocation-same-effect
! Explicit DEALLOCATE without options and automatic procedure-exit deallocation are both observed only by status/reallocation.
module dealloc_automatic_same_effect_m
  implicit none
  integer :: checks = 0
contains
  subroutine automatic_visit(pass)
    integer, intent(in) :: pass
    integer, allocatable :: auto(:)
    integer :: stat
    if (allocated(auto)) error stop 'D9732:auto-same:entry-unallocated'
    checks = checks + 1
    if (pass == 1) then
      allocate(auto(-5:-3), stat=stat)
      if (stat /= 0) error stop 'D9732:auto-same:first-stat'
      auto = [307, 311, 313]
      if (.not. allocated(auto)) error stop 'D9732:auto-same:first-allocated'
      checks = checks + 1
      if (lbound(auto,1) /= -5) error stop 'D9732:auto-same:first-lower'
      checks = checks + 1
      if (ubound(auto,1) /= -3) error stop 'D9732:auto-same:first-upper'
      checks = checks + 1
      if (any(auto /= [307, 311, 313])) error stop 'D9732:auto-same:first-values'
      checks = checks + 1
      return
    end if
    allocate(auto(10:12), stat=stat)
    if (stat /= 0) error stop 'D9732:auto-same:second-stat'
    auto = [317, 331, 337]
    if (lbound(auto,1) /= 10) error stop 'D9732:auto-same:second-lower'
    checks = checks + 1
    if (ubound(auto,1) /= 12) error stop 'D9732:auto-same:second-upper'
    checks = checks + 1
    if (any(auto /= [317, 331, 337])) error stop 'D9732:auto-same:second-values'
    checks = checks + 1
  end subroutine automatic_visit
end module dealloc_automatic_same_effect_m

program dealloc_automatic_same_effect
  use dealloc_automatic_same_effect_m
  implicit none
  integer, allocatable :: explicit(:)
  integer :: stat
  allocate(explicit(-10:-8), stat=stat)
  if (stat /= 0) error stop 'D9732:auto-same:explicit-stat'
  explicit = [293, 299, 301]
  if (.not. allocated(explicit)) error stop 'D9732:auto-same:explicit-before-allocated'
  checks = checks + 1
  if (lbound(explicit,1) /= -10) error stop 'D9732:auto-same:explicit-before-lower'
  checks = checks + 1
  if (ubound(explicit,1) /= -8) error stop 'D9732:auto-same:explicit-before-upper'
  checks = checks + 1
  if (any(explicit /= [293, 299, 301])) error stop 'D9732:auto-same:explicit-before-values'
  checks = checks + 1
  deallocate(explicit)
  if (allocated(explicit)) error stop 'D9732:auto-same:explicit-after-unallocated'
  checks = checks + 1
  allocate(explicit(4:6), stat=stat)
  if (stat /= 0) error stop 'D9732:auto-same:explicit-reallocate-stat'
  explicit = [347, 349, 353]
  if (lbound(explicit,1) /= 4) error stop 'D9732:auto-same:explicit-realloc-lower'
  checks = checks + 1
  if (ubound(explicit,1) /= 6) error stop 'D9732:auto-same:explicit-realloc-upper'
  checks = checks + 1
  if (any(explicit /= [347, 349, 353])) error stop 'D9732:auto-same:explicit-realloc-values'
  checks = checks + 1

  call automatic_visit(1)
  call automatic_visit(2)
  if (checks /= 17) error stop 'D9732:auto-same:check-total'
  write(*,'(a)') 'DEALLOC AUTOMATIC SAME EFFECT OK'
end program dealloc_automatic_same_effect
