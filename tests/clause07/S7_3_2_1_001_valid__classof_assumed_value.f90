! rule: S7.3.2.1-001
! covers: classof-assumed-value classof-derived-kind
! evidence: effect
! standard: f2023
program classof_assumed_value
    implicit none
    integer, parameter :: ik = kind(0)
    type :: packet(k, n)
        integer, kind :: k
        integer, len :: n
        integer(k) :: code
        character(n) :: text
    end type
    type(packet(k=ik, n=3)) :: seed
    seed%code = 3
    seed%text = 'abc'
    call inspect(seed)
contains
    subroutine inspect(source)
        class(packet(k=ik, n=*)), intent(in) :: source
        classof(source), allocatable :: copy
        allocate(copy)
        if (.not. allocated(copy)) error stop 'allocation'
        if (copy%k /= ik .or. kind(copy%code) /= ik) error stop 'kind'
        if (copy%n /= 3 .or. len(copy%text) /= 3) error stop 'length-value'
        copy%code = 7
        copy%text = 'xyz'
        if (copy%code /= 7 .or. copy%text /= 'xyz') error stop 'copy'
        if (source%code /= 3 .or. source%text /= 'abc') error stop 'source'
    end subroutine
end program
