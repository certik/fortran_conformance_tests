! rule: S11.1.3.3-004
! covers: dynamic-type-and-parameters
program ab1133_dynamic_type
  implicit none
  type :: base
    integer :: tag
  end type base
  type, extends(base) :: child
    integer :: extra
  end type child
  class(base), allocatable :: obj
  integer :: observed
  allocate(child :: obj)
  select type (obj)
  type is (child)
    obj%tag=3; obj%extra=88
  end select
  observed=-1
  associate (alias => obj)
    select type (alias)
    type is (child)
      observed=alias%extra
    class default
      observed=-88
    end select
  end associate
  if (observed /= 88) then
    write(*,'(a)') 'DYN'
    error stop
  end if
  write(*,'(a)') 'ASSOCIATE BLOCKS DYNAMIC TYPE OK'

end program ab1133_dynamic_type
