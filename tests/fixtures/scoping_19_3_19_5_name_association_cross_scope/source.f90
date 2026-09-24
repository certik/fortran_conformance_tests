! rule: S19.5.1.1-001
! covers: cross-scope-access-mechanisms
module scoping_use_assoc_provider
  implicit none
  integer :: module_value = 222
end module

program scoping_19_3_19_5_name_association_cross_scope
  use scoping_use_assoc_provider, only: used_value => module_value
  implicit none
  integer :: checks
  integer :: actual_value, host_value, argument_seen, use_seen, host_seen
  checks = 0
  actual_value = 1
  host_value = 333
  argument_seen = -1
  use_seen = -2
  host_seen = -3
  call argument_probe(actual_value)
  use_seen = used_value
  call host_probe()
  if (actual_value /= 111) then
    write(*,'(a)') 'SCOPE:name_association_cross_scope:argument-association'
    error stop
  end if
  checks = checks + 1
  if (argument_seen /= 111) then
    write(*,'(a)') 'SCOPE:name_association_cross_scope:argument-seen'
    error stop
  end if
  checks = checks + 1
  if (use_seen /= 222) then
    write(*,'(a)') 'SCOPE:name_association_cross_scope:use-association'
    error stop
  end if
  checks = checks + 1
  if (host_seen /= 333) then
    write(*,'(a)') 'SCOPE:name_association_cross_scope:host-association'
    error stop
  end if
  checks = checks + 1
  if (checks /= 4) then
    write(*,'(a)') 'SCOPE:name_association_cross_scope:check-count'
    error stop
  end if
  write(*,'(a)') 'SCOPING 19.3-19.5 NAME ASSOCIATION CROSS SCOPE OK'
contains
  subroutine argument_probe(dummy_name)
    integer, intent(inout) :: dummy_name
    dummy_name = 111
    argument_seen = dummy_name
  end subroutine
  subroutine host_probe()
    host_seen = host_value
  end subroutine
end program scoping_19_3_19_5_name_association_cross_scope
