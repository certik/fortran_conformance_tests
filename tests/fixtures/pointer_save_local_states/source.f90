module save_state_targets
  implicit none
  integer, target :: live = 11
end module save_state_targets
program save_local_states
  use save_state_targets
  implicit none
  integer :: checks
  checks = 0
  call visit(1, checks)
  live = 17
  call visit(2, checks)
  call visit(3, checks)
  if (checks /= 16) error stop
  print '(a)', 'SAVE LOCAL STATES OK'
contains
  subroutine visit(phase, checks)
    use save_state_targets
    implicit none
    integer, intent(in) :: phase
    integer, intent(inout) :: checks
    integer, pointer, save :: p
    integer, pointer, save :: q
    integer, allocatable, save :: a(:), empty(:), never(:)
    if (phase == 1) then
      p => live
      nullify(q)
      allocate(a(2))
      a = [11, 13]
      if (allocated(never)) error stop
      checks = checks + 1
      allocate(empty(0))
      return
    else if (phase == 2) then
      if (.not. associated(p, live)) error stop
      checks = checks + 1
      if (p /= 17) error stop
      checks = checks + 1
      if (associated(q)) error stop
      checks = checks + 1
      if (.not. allocated(a)) error stop
      checks = checks + 1
      if (size(a) /= 2) error stop
      checks = checks + 1
      if (a(1) /= 11 .or. a(2) /= 13) error stop
      checks = checks + 1
      a = [17, 19]
      if (allocated(never)) error stop
      checks = checks + 1
      if (.not. allocated(empty)) error stop
      checks = checks + 1
      if (size(empty) /= 0) error stop
      checks = checks + 1
      return
    else
      if (a(1) /= 17 .or. a(2) /= 19) error stop
      checks = checks + 1
      allocate(never(1))
      never = 29
      if (.not. allocated(never)) error stop
      checks = checks + 1
      if (never(1) /= 29) error stop
      checks = checks + 1
      if (.not. allocated(empty)) error stop
      checks = checks + 1
      if (size(empty) /= 0) error stop
      checks = checks + 1
      if (associated(q)) error stop
      checks = checks + 1
    end if
  end subroutine visit
end program save_local_states
