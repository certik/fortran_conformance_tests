! rule: S11.1.3.2-003
! covers: polymorphic-selector-control
program ab1132_polymorphic
  implicit none
  type :: base
    integer :: tag
  end type base
  type, extends(base) :: child
    integer :: extra
  end type child
  class(base), allocatable :: obj
  integer :: seen_tag, seen_extra
  allocate(child :: obj)
  select type (obj)
  type is (child)
    obj%tag=15; obj%extra=26
  end select
  seen_tag=-1; seen_extra=-2
  associate (alias => obj)
    select type (alias)
    type is (child)
      seen_tag=alias%tag
      seen_extra=alias%extra
    class default
      seen_tag=-15
    end select
  end associate
  if (seen_tag /= 15) then
    write(*,'(a)') 'POLYTAG'
    error stop
  end if
  if (seen_extra /= 26) then
    write(*,'(a)') 'POLYEXTRA'
    error stop
  end if
  write(*,'(a)') 'ASSOCIATE BLOCKS POLYMORPHIC OK'

end program ab1132_polymorphic
